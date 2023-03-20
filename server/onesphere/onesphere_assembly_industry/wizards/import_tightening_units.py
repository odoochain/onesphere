# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import xlrd, base64
from odoo.exceptions import UserError, ValidationError
from odoo.tools import ustr
from odoo.addons.onesphere_assembly_industry.constants import (
    ALL_TIGHTENING_TEST_TYPE_LIST,
    EXCEL_TYPE,
    IMG_TYPE,
    CURRENT_PATH,
)
import os
import logging
import pyexcel

_logger = logging.getLogger(__name__)

FIRST_DATA_ROW = 2


class ImportTighteningUnit(models.TransientModel):
    _name = "onesphere.import.tightening.unit"
    _description = "Import Tightening Unit"
    _inherit = ["onesphere.import.mixin"]

    def _import_tightening_unit(self, operation_data):
        for i in range(FIRST_DATA_ROW, len(operation_data)):
            row_data = [content for content in operation_data[i] if content != ""]
            if len(row_data) < 1:
                continue
            tightening_unit_code = row_data[0]
            controller_code = row_data[1]
            controller = self.env["maintenance.equipment"].search(
                [("serial_no", "=", controller_code)]
            )
            if not controller:
                raise ValidationError(
                    _(f"Can Not Found controller,Code %s") % controller_code
                )
            tightening_unit_data = {
                "ref": tightening_unit_code,
                "tightening_controller_id": controller.id,
            }
            self.env["onesphere.tightening.unit"].create(tightening_unit_data)

    def button_import_tightening_unit(self):
        if not self.file:
            raise ValidationError(_("Please Upload A File!"))
        excel_file = base64.b64decode(self.file)
        book = pyexcel.get_book(file_type=self.file_type, file_content=excel_file)
        for sheet in book:
            if len(sheet) <= FIRST_DATA_ROW:
                continue
            try:
                self._import_tightening_unit(sheet)
                self.env.user.notify_success(_("Create Tightening Unit Success"))
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                _logger.error(_(f"Create Tightening Unit Failed,Reason: %s"), ustr(e))
                self.env.user.notify_warning(
                    _(f"%s") % ustr(e),
                    title=_(f"Create Tightening Unit Failed:"),
                    sticky=True,
                )

    def tightening_unit_template_download(self, current_path=CURRENT_PATH):
        template_path = self._context.get("template_path")
        if not template_path:
            raise ValidationError(f"No Template Path!")
        complete_template_path = os.path.join(current_path, template_path)
        if not os.path.exists(complete_template_path):
            raise ValidationError(f"Not Found File: %s !") % complete_template_path
        return {
            "type": "ir.actions.act_url",
            "url": f"/oneshare/template_download?template_path={complete_template_path}",
            "target": "self",
        }
