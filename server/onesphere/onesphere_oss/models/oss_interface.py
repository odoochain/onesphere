# -*- coding: utf-8 -*-
import functools
import io
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from typing import Optional, Union

import urllib3
from minio import Minio
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration
from minio.commonconfig import Filter, ENABLED
from minio.deleteobjects import DeleteObject
from minio.helpers import ObjectWriteResult
from odoo.addons.oneshare_utils.constants import DEFAULT_TIMEOUT
from odoo.addons.oneshare_utils.constants import (
    ENV_OSS_ENDPOINT,
    ENV_OSS_ACCESS_KEY,
    ENV_OSS_SECRET_KEY,
    ENV_MAX_WORKERS,
    ENV_OSS_SECURITY_TRANSPORT,
)

from odoo import models
from odoo.tools import ustr
from odoo.tools.profiler import profile

_logger = logging.getLogger(__name__)


def oss_wrapper(raw_resp=True):
    """

    :param raw_resp: boolean, 是否返回urllib3.HTTPResponse对象
    :return:
    """

    def decorator(f):
        @functools.wraps(f)
        def _oss_wrap(*args, **kw):
            data = None
            resp = None
            _logger.debug("params:%s, object params: %s", args, kw)
            try:
                resp: Optional[ObjectWriteResult, urllib3.response.HTTPResponse] = f(
                    *args, **kw
                )
                if isinstance(resp, ObjectWriteResult):
                    data = resp.object_name
                if isinstance(resp, urllib3.response.HTTPResponse):
                    data = resp.data
            except Exception as e:
                _logger.error("%s: %s", f.__name__, ustr(e))
            finally:
                if not resp:
                    return resp
                if isinstance(resp, urllib3.response.HTTPResponse):
                    resp.close()
                    resp.release_conn()
                if raw_resp:
                    return resp
                return data

        return _oss_wrap

    return decorator


class OSSInterface(models.AbstractModel):
    _name = "onesphere.oss.interface"
    _description = "对象存储接口抽象类"

    def ensure_oss_client(self):
        ICP = self.env["ir.config_parameter"]
        endpoint = ICP.get_param("oss.endpoint", ENV_OSS_ENDPOINT)
        access_key = ICP.get_param("oss.access_key", ENV_OSS_ACCESS_KEY)
        secret_key = ICP.get_param("oss.secret_key", ENV_OSS_SECRET_KEY)
        security = ICP.get_param("oss.security", ENV_OSS_SECURITY_TRANSPORT)
        c = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=security,
            http_client=urllib3.PoolManager(
                timeout=DEFAULT_TIMEOUT,
                maxsize=ENV_MAX_WORKERS * 8,
                retries=urllib3.Retry(
                    total=5,
                    backoff_factor=0.2,
                    status_forcelist=[500, 502, 503, 504],
                ),
            ),
        )
        return c

    # @profile
    def get_oss_objects(
        self, bucket_name: str, object_names: List[str], curve_ids: List[str]
    ):
        # 获取minio数据
        data = {}
        if not object_names:
            return data
        client = self.ensure_oss_client()
        if len(object_names) <= ENV_MAX_WORKERS:
            data.update(
                {
                    curve_id: self.get_oss_object(bucket_name, object_name, client)
                    for object_name, curve_id in zip(object_names, curve_ids)
                }
            )
            return data
        with ThreadPoolExecutor(max_workers=ENV_MAX_WORKERS * 8) as executor:
            task_list = {
                executor.submit(
                    self.get_oss_object, bucket_name, object_name, client
                ): curve_id
                for object_name, curve_id in zip(object_names, curve_ids)
            }
            for task in as_completed(task_list):
                task_exception = task.exception()
                if task_exception:
                    _logger.error("get_oss_objects 任务执行失败: %s", ustr(task_exception))
                    continue
                data.update({task_list[task]: task.result()})
        return data

    @oss_wrapper(raw_resp=False)
    def get_oss_object(
        self, bucket_name: str, object_name: str, client: Union[Minio] = None
    ):
        # 获取minio数据
        if not client:
            client = self.ensure_oss_client()
        ret = client.get_object(bucket_name, object_name)
        return ret

    @oss_wrapper(raw_resp=False)
    def remove_oss_objects(
        self, bucket_name: str, object_names: List[str], client: Union[Minio] = None
    ):
        # 获取minio数据
        if not client:
            client = self.ensure_oss_client()
        objects = [DeleteObject(name) for name in object_names]
        errors = client.remove_objects(bucket_name, objects)
        for error in errors:
            _logger.error(ustr(error))
        return ""

    @oss_wrapper(raw_resp=False)
    def remove_bucket(self, bucket_name: str, client: Union[Minio] = None):
        if not client:
            client = self.ensure_oss_client()
        ret = client.remove_bucket(bucket_name)
        return ret

    @oss_wrapper(raw_resp=True)
    def bucket_exists(self, bucket_name: str, client: Union[Minio] = None):
        if not client:
            client = self.ensure_oss_client()
        return client.bucket_exists(bucket_name)

    @oss_wrapper(raw_resp=True)
    def create_bucket(
        self, bucket_name: str, client: Union[Minio] = None, public=False
    ):
        if not client:
            client = self.ensure_oss_client()
        ret = client.bucket_exists(bucket_name)
        if ret:
            return ret
        try:
            client.make_bucket(bucket_name)
            if public:
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": [
                                "s3:GetBucketLocation",
                                "s3:ListBucket",
                                "s3:ListBucketMultipartUploads",
                            ],
                            "Resource": f"arn:aws:s3:::{bucket_name}",
                        },
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": [
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListMultipartUploadParts",
                                "s3:AbortMultipartUpload",
                            ],
                            "Resource": f"arn:aws:s3:::{bucket_name}/*",
                        },
                    ],
                }
                client.set_bucket_policy(bucket_name, policy=json.dumps(policy))
        except Exception as e:
            msg = f"对象存储: {bucket_name}创建失败: {ustr(e)}"
            _logger.error(msg)
            self.env.user.notify_danger(msg)
            return False
        return True

    def set_lifecycle(self, bucket_name: str, days: int):
        try:
            client = self.ensure_oss_client()
            config = LifecycleConfig(
                [
                    Rule(
                        status=ENABLED,
                        rule_filter=Filter(prefix=""),
                        rule_id="lifecycle_rule",
                        expiration=Expiration(days=days),
                    )
                ],
            )
            client.set_bucket_lifecycle(bucket_name, config)
        except Exception as e:
            msg = f"对象存储: {bucket_name}更新保留策略失败: {ustr(e)}"
            _logger.error(msg)
            self.env.user.notify_danger(msg)

    @oss_wrapper(raw_resp=False)
    def put_oss_object(
        self, bucket_name: str, object_name: str, data: Union[bytes, str]
    ):
        c = self.ensure_oss_client()
        if isinstance(data, str):
            data = data.encode("utf-8")
        length = len(data)
        f = io.BytesIO(data)
        return c.put_object(bucket_name, object_name, f, length)
