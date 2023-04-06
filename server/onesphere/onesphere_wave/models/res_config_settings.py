# -*- coding: utf-8 -*-

import logging

from odoo import fields, models, api, _
from odoo.addons.onesphere_wave.constants import (
    ENV_DOWNLOAD_TIGHTENING_RESULT_ENCODE,
    ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT,
)
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    download_tightening_results_limit = fields.Integer(
        string="Download Tightening Result Records Limit",
        config_parameter="onesphere_wave.download_tightening_results_limit",
        default=ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT,
    )

    download_tightening_results_encode = fields.Char(
        string="Download Tightening Result Records Encode",
        config_parameter="onesphere_wave.download_tightening_results_encode",
        default=ENV_DOWNLOAD_TIGHTENING_RESULT_ENCODE,
    )

    @api.constrains("download_tightening_results_limit")
    def _constraint_download_tightening_results_limit(self):
        for record in self:
            if record.download_tightening_results_limit <= 0:
                raise ValidationError(
                    _("Download tightening results limit must be greater 0")
                )
