# -*- coding: utf-8 -*-
import io
import logging
import os
import tempfile
import zipfile
from distutils.util import strtobool

import docker
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from odoo.addons.oneshare_utils.zip import zip_dir
from odoo.addons.web.controllers.main import Database as webDatabaseController

import odoo
import odoo.modules.registry
import odoo.release
import odoo.sql_db
from odoo import http
from odoo.http import dispatch_rpc
from odoo.service import db
from odoo.tools import ustr
from odoo.tools.misc import str2bool

_logger = logging.getLogger(__name__)

ENV_DOCKER_URL = os.getenv("ENV_DOCKER_URL", "unix://var/run/docker.sock")

ENV_BACKUP_WITH_MINIO = strtobool(os.getenv("ENV_BACKUP_WITH_MINIO", "False"))

try:
    client = docker.DockerClient(base_url=ENV_DOCKER_URL, version="auto")
except Exception as e:
    _logger.error("初始化docker客户端错误: %s", ustr(e))
    client = None

CONTAINER_STOP_TIMEOUT = 20


def restore_minio_data(zip_fn):
    minio_container = None
    if not client:
        return
    containers = client.containers.list()
    for container in containers:
        image_name = container.image.tags[0]
        if "minio" in image_name:
            minio_container = container
            break
    if not minio_container or not ENV_BACKUP_WITH_MINIO:
        return
    with tempfile.TemporaryDirectory() as dump_dir:
        if zipfile.is_zipfile(zip_fn):
            # v8 format
            with zipfile.ZipFile(zip_fn, "r") as z:
                z.extract("backup.tar", dump_dir)
                # 需要关闭重启
                minio_container.stop(timeout=CONTAINER_STOP_TIMEOUT)  # 先关闭容器
                c = client.containers.run(
                    "ubuntu",
                    volumes_from=[minio_container.name],
                    detach=True,
                    volumes=[f"{dump_dir}:/backup"],
                    command="""bash -c "cd /data && tar xvf /backup/backup.tar --strip 1" """,
                )
                exit_status = c.wait()["StatusCode"]
                _logger.info("容器返回值: %s", exit_status)
                c.remove()
                minio_container.start()


def backup_minio_data(stream):
    minio_container = None
    if not client:
        _logger.error("请先初始化docker客户端")
        return
    containers = client.containers.list(filters={"status": "running"})
    for container in containers:
        image_name = container.image.tags[0]
        if "minio" in image_name:
            minio_container = container
            break
        _logger.info("%s", image_name)
    if not minio_container:
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            minio_container.stop(timeout=CONTAINER_STOP_TIMEOUT)  # 先关闭容器
            c = client.containers.run(
                "ubuntu",
                volumes_from=[minio_container.name],
                detach=True,
                volumes=[f"{tmp_dir}:/backup"],
                command="tar cvf /backup/backup.tar /data",
            )
            exit_status = c.wait()["StatusCode"]
            _logger.info("容器返回值: %s", exit_status)
            c.remove()
            minio_container.start()
        except Exception as e:
            _logger.error("%s", ustr(e))
            return
        zip_dir(
            tmp_dir,
            stream,
            mode="a",
            include_dir=False,
            fnct_sort=lambda file_name: file_name != "dump.sql",
        )
        stream.seek(0)


def offline_backup_database(
    db_name="", backup_path=os.path.join(odoo.tools.config["data_dir"], "backup.zip")
):
    """
    离线备份数据库至data_dir下
    @param db_name: 数据库名称
    @param backup_path: 备份文件
    """
    if not db_name:
        db_name = odoo.tools.config["db_name"]
    dump_stream = odoo.service.db.dump_db(db_name, None, "zip")
    if ENV_BACKUP_WITH_MINIO:
        backup_minio_data(dump_stream)
    if os.path.exists(backup_path):
        os.remove(backup_path)  # 删除掉已有备份
    with io.FileIO(backup_path, "w") as f:
        f.write(dump_stream.read())


class Database(webDatabaseController):
    @http.route()
    def backup(self, master_pwd, name, backup_format="zip"):
        resp = super(Database, self).backup(master_pwd, name, backup_format)
        if not resp.is_streamed:
            return resp
        if not ENV_BACKUP_WITH_MINIO:
            return resp
        stream = resp.response
        if ENV_BACKUP_WITH_MINIO:
            backup_minio_data(stream)
        response = werkzeug.wrappers.Response(
            stream, headers=resp.headers, direct_passthrough=True
        )
        return response

    @http.route()
    def restore(self, master_pwd, backup_file, name, copy=False):
        insecure = odoo.tools.config.verify_admin_password("admin")
        if insecure and master_pwd:
            dispatch_rpc("db", "change_admin_password", ["admin", master_pwd])
        try:
            data_file = None
            db.check_super(master_pwd)
            with tempfile.NamedTemporaryFile(delete=False) as data_file:
                backup_file.save(data_file)
            db.restore_db(name, data_file.name, str2bool(copy))
            if ENV_BACKUP_WITH_MINIO:
                restore_minio_data(data_file.name)
            return http.local_redirect("/web/database/manager")
        except Exception as e:
            error = "Database restore error: %s" % (str(e) or repr(e))
            return self._render_template(error=error)
        finally:
            if data_file:
                os.unlink(data_file.name)
