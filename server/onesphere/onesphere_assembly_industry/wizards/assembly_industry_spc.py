# -*- coding: utf-8 -*-
import logging
from typing import List

import numpy as np
from odoo.addons.oneshare_utils.constants import ONESHARE_DEFAULT_SPC_MAX_LIMIT
from odoo.addons.onesphere_assembly_industry.utils import (
    get_dist_echarts_options,
    get_xr_spc_echarts_options,
    _compute_dist_XR_js,
)
from odoo.addons.onesphere_spc.utils.lexen_spc.chart import cmk, cpk, cr, cp
from odoo.addons.onesphere_spc.utils.lexen_spc.plot import normal, histogram
from scipy.stats import exponweib

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.fields import DATETIME_LENGTH

_logger = logging.getLogger(__name__)

measurement_type_field_map = {
    "torque": "measurement_final_torque",
    "angle": "measurement_final_angle",
}

X_LINE = 0
ARRAY_Y = 1
EFF_LENGTH = 2


class OnesphereAssyIndustrySPC(models.TransientModel):
    _name = "onesphere.assy.industry.spc"
    _description = "装配行业拧紧SPC分析"
    _inherit = ["onesphere.spc.mixin"]

    measurement_type = fields.Selection(
        [("torque", "Torque"), ("angle", "Angle")],
        default="torque",
        string="Assembly Industry SPC Measurement Type",
    )

    display_name = fields.Char(default="SPC分析", store=False)

    bolt_id = fields.Many2one("onesphere.tightening.bolt", string="Bolt ID")

    @api.model
    def default_get(self, fields_list):
        res = super(OnesphereAssyIndustrySPC, self).default_get(fields_list)
        if "model_object" in fields_list:
            res.update(
                {
                    "model_object": self.env["ir.model"]
                    .search([("model", "=", "onesphere.tightening.result")])
                    .id
                }
            )
        if "model_object_field" in fields_list:
            res.update(
                {
                    "model_object_field": self.env["ir.model.fields"]
                    ._get_ids("onesphere.tightening.result")
                    .get("measurement_final_torque")
                }
            )
        return res

    @api.onchange("measurement_type")
    def _onchange_measurement_type(self):
        self.ensure_one()
        measurement_type = self.measurement_type
        field_name = measurement_type_field_map[measurement_type]
        self.model_object_field = self.env["ir.model.fields"]._get(
            "onesphere.tightening.result", field_name
        )

    @api.model
    def query_spc(
        self,
        bolt_id=None,
        query_from=None,
        query_to=None,
        query_type="torque",
        usl=10.0,
        lsl=1.0,
        limit=ONESHARE_DEFAULT_SPC_MAX_LIMIT,
        others=None,
        *args,
        **kwargs,
    ):
        if others is None:
            others = {}
        _logger.debug("query spc, params: %s, %s", args, kwargs)
        query_date_from = fields.Datetime.from_string(
            query_from[:DATETIME_LENGTH]
        )  # UTC 时间
        query_date_to = fields.Datetime.from_string(query_to[:DATETIME_LENGTH])
        model_object_param = others.get("model_object", None)
        spc_step = float(others.get("spc_step", None))
        if not model_object_param:
            raise ValidationError("model_object_param is required")
        model_object = self.env["onesphere.tightening.result"]
        query_type_field = query_type
        if not query_type_field:
            raise ValidationError(
                f"query_type: {query_type} is not valid. query_type_field is required"
            )
        data = model_object.get_tightening_result_filter_datetime(
            date_from=query_date_from,
            date_to=query_date_to,
            field=query_type_field,
            bolt_id=bolt_id,
            limit=limit,
        )
        _logger.debug(_(f"Spc Data of Query Result: {data}"))

        data_list = data[query_type]

        # data_list = list(filter(lambda d: d, data_list))

        CMK = cmk(data_list, usl, lsl)
        CPK = cpk(data_list, usl, lsl)
        CP = cp(data_list, usl, lsl)
        CR = cr(data_list, usl, lsl)

        # 正态分布数据
        x1, y1, y2, eff_length = self._compute_dist_js(data_list, usl, lsl, spc_step)
        dict_norm = {"x1": x1, "y1": y1, "y2": y2}

        if len(data) > 0:
            description = (
                f"拧紧点数量(count):{eff_length}/{len(data_list)}, 均值(mean):{np.mean(data_list) or 0:.2f}, 标准差(sigma):{np.std(data_list) or 0:.2f}\n\n"
                f"原始数据范围(range):[{np.min(data_list) or 0:.2f},{np.max(data_list) or 0:.2f}]"
            )
            # f'6sigma数据范围: []'
        else:
            description = "拧紧点数量: 0"

        dict_xr_chart = _compute_dist_XR_js(data_list)

        # nok_data = model_object.get_tightening_result_filter_datetime(date_from=query_date_from, date_to=query_date_to,
        #                                                               filter_result='nok',
        #                                                               field=query_type_field,
        #                                                               limit=limit)
        # nok_data_list = nok_data[query_type]
        # x1, y1, y2 = self._compute_weill_dist_js(nok_data_list)
        # dict_weill_dict = {
        #     'x1': x1,
        #     'y1': y1,
        #     'y2': y2
        # }

        ret = {
            "pages": {
                "o_spc_norm_dist": get_dist_echarts_options(
                    dict_norm, query_type, description
                ),
                # 'o_spc_weibull_dist': get_dist_echarts_options(dict_weill_dict, query_type, description,
                #                                                type='weill'),
                # 'o_spc_scatter': self.get_scatter_echarts_options(),
                "o_spc_xr_chart": get_xr_spc_echarts_options(
                    dict_xr_chart, query_type, description
                ),
            },
            "cmk": CMK if CMK else 0.0,
            "cpk": CPK if CPK else 0.0,
            "cp": CP if CP else 0.0,
            "cr": CR if CR else 0.0,
        }

        return ret

    @staticmethod
    def _compute_dist_js(
        data_list: List[float], usl: float, lsl: float, spc_step: float
    ):
        histogram_data = histogram(data_list, usl, lsl, spc_step)
        normal_data = normal(data_list, usl, lsl, spc_step)
        x_axis_data, y_histogram_data, y_normal_data = [], [], []
        x_line_len = len(histogram_data[X_LINE])
        for i in range(x_line_len - 1):
            # 取x轴数据生成区间，并生成对应区间的直方图数据和正太分布数据，故循环长度为x轴数据长度减1
            x_axis_data.append(
                f"{histogram_data[X_LINE][i]:.1f},{histogram_data[X_LINE][i + 1]:.1f}"
            )
            y_histogram_data.append(round(histogram_data[ARRAY_Y][i] * 100, 2))
            y_normal_data.append(round(normal_data[ARRAY_Y][i] * 100, 2))
        return x_axis_data, y_histogram_data, y_normal_data, histogram_data[EFF_LENGTH]

    @staticmethod
    def _compute_weill_dist_js(nok_data_list: List[float]):
        # floc, fscale = exponweib.fit_loc_scale(nok_data_list)
        data_len = len(nok_data_list)
        a, c, loc, scale = exponweib.fit(nok_data_list)
        bins = np.linspace(np.min(nok_data_list), np.max(nok_data_list) + 0.5, num=10)
        hist, bin_edges = np.histogram(nok_data_list, bins=bins)
        x_axis_data, y_histogram_data, y_normal_data = [], [], []
        y_pdf = exponweib(a, c, loc, scale).pdf(bin_edges).tolist()
        for i in range(len(bin_edges) - 1):
            x_axis_data.append(f"{bin_edges[i]:.1f},{bin_edges[i + 1]:.1f}")
            y_histogram_data.append(round(hist[i] / data_len * 100, 2))
            y_normal_data.append(round(y_pdf[i] * 100, 2))
        return x_axis_data, y_histogram_data, y_normal_data

    @api.model
    def open_spc_analyze_view(self):
        return {
            "name": "SPC分析",
            "view_mode": "form",
            "res_model": self._name,
            "type": "ir.actions.act_window",
            "context": self.env.context,
        }
