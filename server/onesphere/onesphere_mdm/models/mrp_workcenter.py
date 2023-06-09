# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    workcenter_id = fields.Many2one(
        "mrp.workcenter",
        string="Work Center",
        required=False,
        check_company=True,
        ondelete="cascade",
    )  # 同时删除相关记录


class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    section_id = fields.Many2one(
        "oneshare.mrp.work.area",
        string="Production Section",
        index=True,
        ondelete="restrict",  # 不允许删除工段
        domain=lambda self: "[('company_id', '=', company_id), ('category_id', '=', {})]".format(
            self.env.ref("onesphere_mdm.oneshare_work_area_category_3").id
        ),
    )

    related_work_area_id = fields.Many2one(
        "oneshare.mrp.work.area",
        string="Related Work Area",
        ondelete="cascade",
        domain=lambda self: "[('company_id', '=', company_id), ('category_id', '=', {})]".format(
            self.env.ref("onesphere_mdm.oneshare_work_area_category_4").id
        ),
    )

    group_ids = fields.Many2many(
        "mrp.workcenter.group",
        "mrp_workcenter_group_rel",
        "workcenter_id",
        "group_id",
        string="Work Center Groups",
    )

    def name_get(self):
        res = []
        for workcenter in self:
            name = f"[{workcenter.code}]{workcenter.name}"
            res.append((workcenter.id, name))
        return res

    def toggle_active(self):
        ret = super(MrpWorkcenter, self).toggle_active()
        related_work_area_ids = self.mapped("related_work_area_id")
        if related_work_area_ids:
            related_work_area_ids.toggle_active()
        return ret

    def action_open_related_work_area_form_view(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "onesphere_mdm.oneshare_action_open_work_station"
        )
        view_id = self.env.ref("onesphere_mdm.oneshare_mom_work_area_view_form").id
        action.update(
            {
                "res_id": self.related_work_area_id.id,
                "views": [[view_id, "form"]],
                "view_mode": "form",
            }
        )
        return action

    def create_related_work_station_area(self):
        self.ensure_one()
        val = {
            "code": self.code,
            "name": self.name,
            "time_efficiency": self.time_efficiency,
            "parent_id": self.section_id.id,
        }
        ret = self.env["oneshare.mrp.work.area"].create_work_station(val)
        return ret

    @api.model_create_multi
    def create(self, vals_list):
        ret = super(MrpWorkcenter, self).create(vals_list)
        if not ret:
            return ret
        for rec in ret:
            if not rec.related_work_area_id:
                work_station_area = rec.create_related_work_station_area()
                rec.write({"related_work_area_id": work_station_area.id})
        return ret

    def write(self, vals):
        ret = super(MrpWorkcenter, self).write(vals)
        return ret
