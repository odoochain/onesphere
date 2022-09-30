# -*- coding: utf-8 -*-
import numpy as np
from dateutil.relativedelta import relativedelta
from odoo.addons.onesphere_assembly_industry.constants import ENV_PROCESS_PROPOSAL_DURATION, \
    ENV_PROCESS_PROPOSAL_ANGLE_MARGIN
from odoo.addons.onesphere_assembly_industry.utils import get_norm_dist_echarts_options

from odoo import fields, models


class OnesphereTighteningBolt(models.Model):
    _name = "onesphere.tightening.bolt"
    _description = 'Tightening Bolt Model'

    name = fields.Char(string='Name', required=True, copy=False)
    description = fields.Html(string='Description', copy=True)
    type = fields.Selection([('missing', 'Missing'), ('verified', 'Verified')], string='Type', default='verified',
                            required=True)
    bolt_result_rel = fields.One2many('onesphere.tightening.result', 'tightening_point_name', string='Bolt Result Rel')

    _sql_constraints = [('name_uniq', 'unique (name)', "bolt name already exists !")]

    def button_open_tightening_process_proposal_analysis(self):
        self.ensure_one()
        query_type = 'angle'
        icp = self.env['ir.config_parameter'].sudo()
        tightening_process_proposal_duration = icp.get_param("oneshare.tightening.process.proposal.duration",
                                                             ENV_PROCESS_PROPOSAL_DURATION)  # 建议计算间隔天数
        results_obj = self.env['onesphere.tightening.result']
        query_date_from = fields.Datetime.today() - relativedelta(days=tightening_process_proposal_duration)
        data = results_obj.get_tightening_result_filter_datetime(date_from=query_date_from, field=query_type,
                                                                 bolt_id=self.id)
        angles = data.get(query_type, [])
        mean = np.mean(angles)
        std = np.std(angles)
        if len(data) > 0:
            description = f'标准差:{std or 0:.2f}\n' \
                          f'均值:{mean or 0:.2f}\n' \
                          f'建议目标角度范围:[{mean - ENV_PROCESS_PROPOSAL_ANGLE_MARGIN * std or 0:.0f} - ' \
                          f'{mean + ENV_PROCESS_PROPOSAL_ANGLE_MARGIN * std or 0:.0f}]'
        else:
            description = '拧紧点数量: 0'

        angle_hist_y, angle_x_bin_edges = np.histogram(angles, bins=10)
        o_angle_hist = get_norm_dist_echarts_options(data={'x1': angle_x_bin_edges.tolist(), 'y1': angle_hist_y.tolist()},
                                                     query_type=query_type,
                                                     description=description)
        ret = {'pages': {'o_angle_hist': o_angle_hist}}
        return ret
