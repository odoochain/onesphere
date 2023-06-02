# -*- coding: utf-8 -*-
from odoo.addons.onesphere_assembly_industry.constants import (
    DEFAULT_BOLT_NAME_RULES,
    ENV_PROCESS_PROPOSAL_DURATION,
    DEFAULT_ENTITY_ID_RULES,
    TIGHTENING_RESULT_RETENTION_DAYS,
)
from odoo.addons.oneshare_odoo_modify.model import do_add_retention_policy

from odoo import fields, models, api, _
import logging
from odoo.tools import ustr
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    bolt_name_rules = fields.Char(
        default=DEFAULT_BOLT_NAME_RULES,
        string="螺栓编号拼接规则",
        help="the rules of bolt name",
        config_parameter="oneshare.bolt_name.rules",
    )

    tightening_process_proposal_duration = fields.Integer(
        default=ENV_PROCESS_PROPOSAL_DURATION,
        string="拧紧工艺建议计算间隔时间(天)",
        help="拧紧工艺建议计算间隔时间, 默认为三十天",
        config_parameter="oneshare.tightening.process.proposal.duration",
    )

    entity_id_rules = fields.Char(
        default=DEFAULT_ENTITY_ID_RULES,
        string="曲线ID拼接规则",
        help="the rules of curve id",
        config_parameter="oneshare.entity_id.rules",
    )

    tightening_result_retention_policy = fields.Integer(
        default=TIGHTENING_RESULT_RETENTION_DAYS,
        string="拧紧结果保留策略(天)",
        help="the retention policy of tightening result",
        config_parameter="oneshare.tightening_result.retention_policy",
    )

    def remove_all_operations(self):
        try:
            screw = self.env["product.product"].search(
                [
                    (
                        "categ_id",
                        "=",
                        self.env.ref(
                            "onesphere_assembly_industry.product_category_7"
                        ).id,
                    )
                ]
            )
            sql = "DELETE FROM public.onesphere_mrp_bom_operation_rel WHERE 1=1;"
            sql1 = "DELETE FROM public.onesphere_mrp_operation_step_rel WHERE 1=1;"
            sql2 = "DELETE FROM public.mrp_routing_workcenter WHERE 1=1;"
            sql3 = "DELETE FROM public.onesphere_tightening_opr_point WHERE 1=1;"
            sql4 = "DELETE FROM public.oneshare_quality_point WHERE 1=1;"

            self._cr.execute(sql)
            self._cr.execute(sql1)
            self._cr.execute(sql2)
            self._cr.execute(sql3)
            self._cr.execute(sql4)
            self._cr.commit()
            screw.unlink()
            self.env.user.notify_success("删除历史作业成功!!!")
        except Exception as e:
            msg = f"删除历史拧紧结果错误: {ustr(e)}"
            self.env.user.notify_danger(msg)
            _logger.warning(msg)

    @api.constrains("tightening_process_proposal_duration")
    def _constraint_tightening_process_proposal_duration(self):
        for record in self:
            if record.tightening_process_proposal_duration <= 0:
                raise ValidationError(
                    _("Tightening process proposal duration must be greater 0")
                )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        do_add_retention_policy(
            self.env.cr,
            "onesphere_tightening_result",
            f"{self.tightening_result_retention_policy} days",
        )
