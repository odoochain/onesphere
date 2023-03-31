# -*- coding: utf-8 -*-
import logging

import numpy as np
from odoo.addons.oneshare_utils.constants import ONESHARE_DEFAULT_SPC_MAX_LIMIT
from odoo.addons.onesphere_assembly_industry.utils import get_dist_echarts_options

from odoo import api, fields, models
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


class OnesphereAssyFailureAnalysis(models.TransientModel):
    _name = "onesphere.assy.failure.analysis"
    _description = "装配行业拧紧SPC分析"
    _inherit = ["onesphere.assy.industry.spc"]

    display_name = fields.Char(default="失效分析", store=False)

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
        query_date_from = fields.Datetime.from_string(
            query_from[:DATETIME_LENGTH]
        )  # UTC 时间
        query_date_to = fields.Datetime.from_string(query_to[:DATETIME_LENGTH])
        model_object_param = others.get("model_object", None)
        if not model_object_param:
            raise ValidationError("model_object_param is required")
        model_object = self.env["onesphere.tightening.result"]
        query_type_field = query_type
        if not query_type_field:
            raise ValidationError(
                f"query_type: {query_type} is not valid. query_type_field is required"
            )

        nok_data = model_object.get_tightening_result_filter_datetime(
            date_from=query_date_from,
            date_to=query_date_to,
            filter_result="nok",
            field=query_type_field,
            bolt_id=bolt_id,
            limit=limit,
        )

        nok_data_list = nok_data[query_type]

        if len(nok_data_list) > 0:
            description = (
                f"拧紧点数量:{len(nok_data_list)}, 标准差:{np.std(nok_data_list) or 0:.2f}, 均值:{np.mean(nok_data_list) or 0:.2f}\n\n"
                f"原始数据范围:[{np.min(nok_data_list) or 0:.2f},{np.max(nok_data_list) or 0:.2f}]"
            )
        else:
            description = "拧紧点数量: 0"
        x1, y1, y2 = self._compute_weill_dist_js(nok_data_list)
        dict_weill_dict = {"x1": x1, "y1": y1, "y2": []}

        ret = {
            "pages": {
                "o_spc_weibull_dist": get_dist_echarts_options(
                    dict_weill_dict, query_type, description
                ),
            },
            "title": "失效分析成功!!!",
        }

        return ret
