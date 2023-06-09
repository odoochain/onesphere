# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import pycompat, ustr
import logging
from typing import Dict, Tuple

_logger = logging.getLogger(__name__)


class OneshareMrpWorkArea(models.Model):
    _name = "oneshare.mrp.work.area"
    _log_access = False
    _description = "Manufacturing Work Area"
    # _rec_name = 'complete_name'
    _order = "sequence, id"
    _inherit = ["resource.mixin"]
    _check_company_auto = True

    DEFAULT_TYPE_DICT = {
        "search_default_is_shop_floor": "search_default_is_production_line",
        "search_default_is_production_line": "search_default_is_work_segment",
        "search_default_is_work_segment": "search_default_is_work_station",
        "search_default_is_work_station": "search_default_is_workstation_unit",
    }

    AREA_CATEGORY_NUM_DICT = {
        "search_default_is_shop_floor": "onesphere_mdm.oneshare_work_area_category_1",
        "search_default_is_production_line": "onesphere_mdm.oneshare_work_area_category_2",
        "search_default_is_work_segment": "onesphere_mdm.oneshare_work_area_category_3",
        "search_default_is_work_station": "onesphere_mdm.oneshare_work_area_category_4",
        "search_default_is_workstation_unit": "onesphere_mdm.oneshare_work_area_category_5",
    }

    WORK_AREA_CATEGORY_DICT = {
        "search_default_is_production_line": "onesphere_mdm.oneshare_work_area_category_1",
        "search_default_is_work_segment": "onesphere_mdm.oneshare_work_area_category_2",
        "search_default_is_work_station": "onesphere_mdm.oneshare_work_area_category_3",
        "search_default_is_workstation_unit": "onesphere_mdm.oneshare_work_area_category_4",
    }

    @api.depends("name", "code", "parent_id.complete_name")
    def _compute_complete_name(self):
        for area in self:
            complete_name = f"[{area.code}]{area.name}"
            if area.parent_id:
                area.complete_name = f"%s / %s" % (
                    area.parent_id.complete_name,
                    complete_name,
                )
            else:
                area.complete_name = complete_name

    # resource
    complete_name = fields.Char(
        "Complete Name", compute=_compute_complete_name, store=True
    )

    name = fields.Char(
        "Work Area", related="resource_id.name", store=True, readonly=False
    )
    time_efficiency = fields.Float(
        "Time Efficiency",
        related="resource_id.time_efficiency",
        default=100,
        store=True,
        readonly=False,
    )
    active = fields.Boolean(
        "Active", related="resource_id.active", default=True, store=True, readonly=False
    )

    code = fields.Char("Code", copy=False)

    sequence = fields.Integer(
        "Sequence",
        default=1,
        required=True,
        help="Gives the sequence order when displaying a list of work area.",
    )

    parent_id = fields.Many2one(
        "oneshare.mrp.work.area",
        string="Parent Work Area",
        index=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    child_ids = fields.One2many(
        "oneshare.mrp.work.area", "parent_id", string="Child Work Areas"
    )

    related_workcenter_ids = fields.One2many(
        "mrp.workcenter", "related_work_area_id", string="Related Work Center(Station)"
    )

    category_id = fields.Many2one(
        "oneshare.mrp.work.area.category", "Work Area Category", required=True
    )

    technical_name = fields.Char(
        "Category Name", related="category_id.name", store=True, readonly=True
    )

    children_count = fields.Integer(
        "Count Of Work Production Line", compute="_compute_children_count"
    )

    _sql_constraints = [
        (
            "category_code_uniq",
            "unique (code, category_id)",
            "The code must be unique per category !",
        ),
    ]

    def name_get(self):
        res = []
        for area in self:
            name = area.complete_name or area.name
            res.append((area.id, name))
        return res

    # @api.onchange('category_id')
    # def _onchange_category_id(self):
    #     self.ensure_one()
    #     category_id = self.category_id.id if self.category_id else 0
    #     if not self._onchange_category_id:
    #         return {}
    #
    #     if category_id == self.env.ref('onesphere_mdm.oneshare_work_area_category_4').id:
    #         return {'domain': {
    #             'parent_id': [('category_id', '=', self.env.ref('onesphere_mdm.oneshare_work_area_category_3').id)]}}
    #     return {}

    @api.model
    def create_work_station(self, val):
        val.update(
            {
                "category_id": self.env.ref(
                    "onesphere_mdm.oneshare_work_area_category_4"
                ).id
            }
        )
        rec = self.create(val)
        return rec

    def toggle_active(self):
        super(OneshareMrpWorkArea, self).toggle_active()
        related_workcenter_ids = self.mapped("related_workcenter_ids")
        if related_workcenter_ids:
            related_workcenter_ids.toggle_active()
        children_ids = self.mapped("child_ids")
        if children_ids:
            children_ids.toggle_active()

    @staticmethod
    def dry_try_update_context(dict_name, context):
        ret = []
        for key, val in dict_name.items():
            if context.get(key):
                ret.append((key, val))
        if len(ret) > 1:
            raise ValueError(
                _(
                    f"dry_try_update_context error: Need Update Records More Than One: {ret}"
                )
            )
        return ret

    def action_open_children_work_area_update_context(self, context):
        # FIXME: 重构
        need_update_items = self.dry_try_update_context(self.DEFAULT_TYPE_DICT, context)
        if len(need_update_items) == 0:
            return
        vv: Tuple = need_update_items[0]
        key, val = vv
        context.update({val: 1})
        context.pop(key)

    def action_open_related_work_center_form_view(self):
        self.ensure_one()
        if not self.related_workcenter_ids:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "mrp.workcenter",
            "views": [[self.env.ref("mrp.mrp_workcenter_view").id, "form"]],
            "res_id": self.related_workcenter_ids.ids[0],
            "target": "main",
        }

    def action_open_children_work_area_tree_view(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.update(
            {
                "search_default_parent_id": self.id,
            }
        )
        self.action_open_children_work_area_update_context(context)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "onesphere_mdm.oneshare_action_open_shop_floor"
        )
        action["context"] = context
        return action

    @api.depends("child_ids")
    def _compute_children_count(self):
        for area in self:
            area.children_count = len(area.child_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(
            OneshareMrpWorkArea, self.with_context(default_resource_type="area")
        ).create(vals_list)
        return records

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(OneshareMrpWorkArea, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type != "form":
            return res
        context = self.env.context
        fields = res.get("fields")
        if not fields:
            return res
        # 增加关于父节点的动态domain
        if fields.get("parent_id"):
            domain = [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.env.company.id),
            ]
            need_update_items = self.dry_try_update_context(
                self.WORK_AREA_CATEGORY_DICT, context
            )
            if len(need_update_items) == 0:
                return res
            vv: Tuple = need_update_items[0]
            key, val = vv
            domain += [
                ("category_id", "=", self.env.ref(val, raise_if_not_found=True).id)
            ]
            ss = pycompat.to_text(domain)
            res["fields"]["parent_id"]["domain"] = ss
        return res

    @api.model
    def default_get(self, fields_list):
        ret = super(OneshareMrpWorkArea, self).default_get(fields_list)
        context = self.env.context
        if "resource_calendar_id" in fields_list:
            try:
                ret.update(
                    {
                        "resource_calendar_id": self.env.ref(
                            "onesphere_core.resource_calendar_std_140h",
                            raise_if_not_found=True,
                        ).id
                    }
                )
            except Exception as e:
                _logger.error(ustr(e))

        need_update_items = self.dry_try_update_context(
            self.AREA_CATEGORY_NUM_DICT, context
        )
        if len(need_update_items) == 0:
            return ret
        vv: Tuple = need_update_items[0]
        key, val = vv
        ret.update({"category_id": self.env.ref(val).id})
        return ret


class OneshareWorkAreaCategory(models.Model):
    _name = "oneshare.mrp.work.area.category"
    _log_access = False
    _description = "Work Area Category"
    _inherit = ["oneshare.category.mixin"]

    active = fields.Boolean(
        "Active",
        default=True,
        help="If the active field is set to False, it will allow you to hide the category without removing it.",
    )
