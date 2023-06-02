# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizards
from .constants import TIGHTENING_RESULT_RETENTION_DAYS
from odoo.addons.oneshare_odoo_modify.model import do_add_retention_policy


# 增加拧紧结果表保留策略
def _assembly_industry_post_init(cr, registry):
    do_add_retention_policy(
        cr, "onesphere_tightening_result", f"{TIGHTENING_RESULT_RETENTION_DAYS} days"
    )
