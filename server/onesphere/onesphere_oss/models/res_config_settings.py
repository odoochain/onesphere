# -*- coding: utf-8 -*-
import logging

from odoo.addons.oneshare_utils.constants import (
    ENV_OSS_BUCKET,
    ENV_OSS_ENDPOINT,
    ENV_OSS_ACCESS_KEY,
    ENV_OSS_SECRET_KEY,
    ENV_OSS_SECURITY_TRANSPORT,
    ENV_OSS_EXPIRATION_DAYS,
)

from odoo import fields, models
from odoo.tools import ustr
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def create_bucket(self):
        bucket_name = self.oss_bucket_name
        try:
            oss_interface = self.env["onesphere.oss.interface"]
            ret = oss_interface.create_bucket(bucket_name)
            if ret:
                oss_interface.set_lifecycle(bucket_name, self.oss_expiration_days)
                self.env.user.notify_info(f"对象存储: {bucket_name}已创建")
            else:
                raise UserError("创建失败!!!")
        except Exception as e:
            msg = f"对象存储: {bucket_name}创建失败: {ustr(e)}"
            _logger.error(msg)
            self.env.user.notify_danger(msg)

    def bucket_existed(self):
        bucket_name = self.oss_bucket_name
        try:
            oss_interface = self.env["onesphere.oss.interface"]
            existed = oss_interface.bucket_exists(bucket_name)
            if existed:
                self.env.user.notify_info(f"对象存储: {bucket_name}已存在")
            else:
                self.env.user.notify_danger(f"对象存储: {bucket_name}不存在!!!")
        except Exception as e:
            msg = ustr(e)
            _logger.error(msg)
            self.env.user.notify_danger(msg)

    oss_bucket_name = fields.Char(
        default=ENV_OSS_BUCKET, string="OSS Bucket Name", config_parameter="oss.bucket"
    )

    oss_endpoint = fields.Char(
        default=ENV_OSS_ENDPOINT, string="OSS Endpoint", config_parameter="oss.endpoint"
    )

    oss_access_key = fields.Char(
        default=ENV_OSS_ACCESS_KEY,
        string="OSS Access Key",
        config_parameter="oss.access_key",
    )

    oss_secret_key = fields.Char(
        default=ENV_OSS_SECRET_KEY,
        string="OSS Secret Key",
        config_parameter="oss.secret_key",
    )

    oss_security = fields.Boolean(
        default=ENV_OSS_SECURITY_TRANSPORT,
        string="OSS Security Transport(SSL)",
        config_parameter="oss.security",
    )

    oss_expiration_days = fields.Integer(
        default=ENV_OSS_EXPIRATION_DAYS,
        string="OSS Expiration Days(days)",
        config_parameter="oss.expiration_days",
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        oss_interface = self.env["onesphere.oss.interface"]
        existed = oss_interface.bucket_exists(self.oss_bucket_name)
        if existed:
            oss_interface.set_lifecycle(self.oss_bucket_name, self.oss_expiration_days)
