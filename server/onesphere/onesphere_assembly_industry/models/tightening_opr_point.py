# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import uuid


class TighteningOprPointGroup(models.Model):
    _name = "onesphere.tightening.opr.point.group"
    _log_access = False

    _description = "螺栓拧紧点组(多轴)"

    _order = "sequence"

    sequence = fields.Integer("sequence", default=1)

    proposal_key_num = fields.Integer(default=0, copy=False)

    name = fields.Char(
        "Operation Point Group",
        required=True,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "tightening.operation.point.group"
        ),
    )
    key_num = fields.Integer(
        string="Tightening Key Point Count",
        copy=False,
        compute="_compute_key_point_count",
        inverse="_inverse_key_point_count",
        store=True,
    )

    quality_point_id = fields.Many2one(
        "oneshare.quality.point", ondelete="cascade", index=True
    )

    operation_point_ids = fields.One2many(
        "onesphere.tightening.opr.point",
        "group_id",
        string="Tightening Points",
        copy=False,
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique(name)",
            "Tightening Operation Point Group Name MUST BE Unique!",
        )
    ]

    def _inverse_key_point_count(self):
        for record in self:
            record.proposal_key_num = record.key_num

    @api.constrains("key_num")
    def _constraint_key_num(self):
        for record in self:
            lk = len(record.operation_point_ids.filtered(lambda r: r.is_key))
            if record.key_num < lk:
                raise ValidationError(
                    _("Key Point Number Can Not Less Than Operation Point Key Total")
                )

    @api.depends("operation_point_ids.is_key", "proposal_key_num")
    def _compute_key_point_count(self):
        for record in self:
            lk = len(record.operation_point_ids.filtered(lambda r: r.is_key))
            record.key_num = max(record.proposal_key_num, lk)


class TighteningOprPoint(models.Model):
    _name = "onesphere.tightening.opr.point"
    _log_access = False

    _description = "螺栓拧紧点"

    _order = "group_sequence, sequence"

    is_key = fields.Boolean(string="Is Key Tightening Point", default=False)
    active = fields.Boolean(
        "Active",
        default=True,
        help="If the active field is set to False, it will allow you to hide the bills of material without removing it.",
    )

    sequence = fields.Integer("sequence", default=1)

    # name = fields.Char('Tightening Point Name(Bolt Number)',
    #                    default=lambda self: str(uuid.uuid4()))  # 如果未定义拧紧点编号，即自动生成uuid号作为唯一标示,螺栓编号
    bolt_id = fields.Many2one(
        "onesphere.tightening.bolt", ondelete="cascade", delegate=True, required=True
    )
    group_id = fields.Many2one(
        "onesphere.tightening.opr.point.group",
        string="Tightening Point Group",
        help="拧紧组定义，当多轴或者多人同时作业时使用",
    )

    group_sequence = fields.Integer(
        string="Group Sequence for Multi Spindle", help="拧紧组定义，当多轴或者多人同时作业时使用,定义其顺序"
    )

    product_id = fields.Many2one(
        "product.product",
        "Consume Product(Tightening Bolt/Screw)",
        domain="[('categ_id.name', '=', 'Bolt')]",
    )  # 只显示螺栓类型

    product_qty = fields.Float(
        "Product Quantity", default=1.0, digits="Product Unit of Measure"
    )

    x_offset = fields.Float(
        "x axis offset from left(%)",
        default=0.0,
        digits="Unit of Tightening Opr Point Offset",
    )

    y_offset = fields.Float(
        "y axis offset from top(%)",
        default=0.0,
        digits="Unit of Tightening Opr Point Offset",
    )

    tightening_pset = fields.Integer(string="Program Number(Pset/Job)")

    control_mode = fields.Selection(
        [("pset", "Parameter Set"), ("job", "Assembly Process")],
        default="pset",
        string="Control Mode For Tightening",
    )

    parent_quality_point_id = fields.Many2one(
        "oneshare.quality.point",
        ondelete="cascade",
        index=True,
        domain=lambda self: [
            (
                "test_type_id",
                "in",
                (
                    self.env.ref("onesphere_assembly_industry.test_type_tightening").id,
                    self.env.ref(
                        "onesphere_assembly_industry.test_type_tightening_promiscuous"
                    ).id,
                ),
            )
        ],
        string="Quality Control Point(Tightening Operation Step)",
    )
    parent_quality_point_display_name = fields.Char(
        related="parent_quality_point_id.display_name", store=True
    )

    # test_type_id = fields.Many2one('oneshare.quality.point.test_type',
    #                                default=lambda self: self.env.ref(
    #                                    'onesphere_assembly_industry.test_type_tightening_point'))

    max_attempt_times = fields.Integer(
        string="Tightening Operation Max Attempt Times", default=3
    )

    # 测量相关
    # norm = fields.Float('Norm', related='quality_point_id.norm', digits='Quality Tests', inherited=True)
    # tolerance_min = fields.Float('Min Tolerance', related='quality_point_id.tolerance_min',
    #                              digits='Quality Tests', inherited=True)
    # tolerance_max = fields.Float('Max Tolerance', related='quality_point_id.tolerance_max',
    #                              digits='Quality Tests', inherited=True)
    #
    # norm_degree = fields.Float('Norm Degree', related='quality_point_id.norm_degree', inherited=True,
    #                            digits='Quality Tests')  # TDE RENAME ?
    # tolerance_min_degree = fields.Float('Degree Min Tolerance', related='quality_point_id.tolerance_min_degree', inherited=True,
    #                                     digits='Quality Tests', default=0.0)
    # tolerance_max_degree = fields.Float('Degree Max Tolerance', related='quality_point_id.tolerance_max_degree', inherited=True,
    #                                     digits='Quality Tests', default=0.0)

    # 拧紧工具相关
    tightening_tool_ids = fields.Many2many(
        "mrp.workcenter.group.tightening.tool",
        "tightening_point_tool_rel",
        "point_id",
        "tightening_tool_id",
        string="Tightening Tools",
        copy=False,
    )

    # tightening_tool_id = fields.Many2one('maintenance.equipment', string='Prefer Tightening Tool',
    #                                      domain=[('technical_name', 'in', ASSEMBLY_TOOLS_TECH_NAME)],
    #                                      copy=False)

    # 拧紧单元
    tightening_units = fields.Many2many(
        "onesphere.tightening.unit",
        "tightening_point_unit_rel",
        "point_id",
        "tightening_unit_id",
        string="Tightening Units",
    )

    # _sql_constraints = [
    #     ('name_uniq', 'unique(name)', 'Tightening Operation Point Name MUST BE Unique!')]

    @api.constrains("max_attempt_times")
    def _constraint_max_attempt_times(self):
        for record in self:
            if record.max_attempt_times <= 0:
                raise ValidationError(_("Max attempt times must bigger than 0"))
