# -*- coding: utf-8 -*-

from odoo import models, fields
import os

ENV_DEFAULT_LANGUAGE = os.getenv('ENV_DEFAULT_LANGUAGE', 'zh_CN')
ENV_DEFAULT_TIMEZONE = os.getenv('ENV_DEFAULT_TIMEZONE', 'Asia/Shanghai')


class Partner(models.Model):
    _inherit = "res.partner"

    tz = fields.Selection(default=ENV_DEFAULT_TIMEZONE)
    lang = fields.Selection(default=ENV_DEFAULT_LANGUAGE)
