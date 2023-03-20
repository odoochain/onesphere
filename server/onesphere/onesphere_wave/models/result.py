# -*- coding: utf-8 -*-
import itertools
import json
import logging
import os

from boltons.cacheutils import LRU

from odoo import _
from odoo.tools import ustr

from odoo.addons.onesphere_wave.constants import EXCEL_TYPE

_wave_cache = LRU(max_size=128)

logger = logging.getLogger(__name__)

ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT = int(
    os.getenv("ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT", "1000")
)


def _create_wave_result_dict(x, data):
    if not data:
        return False
    else:
        _data = json.loads(data)
    _data["name"] = x.split(".")[0]
    _wave_cache[x] = _data  # 将其加入缓存

    return _data


try:
    from odoo.models import OneshareHyperModel as HModel
except ImportError:
    from odoo.models import Model as HModel


class OperationResult(HModel):
    _inherit = "onesphere.tightening.result"

    def download_tightening_results(self, file_type=EXCEL_TYPE):
        records = self
        ICP = self.env["ir.config_parameter"].sudo()
        download_tightening_results_limit = int(
            ICP.get_param(
                "onesphere_wave.download_tightening_results_limit",
                default=ENV_DOWNLOAD_TIGHTENING_RESULT_LIMIT,
            )
        )
        if len(self) > download_tightening_results_limit:
            self.env.user.notify_warning(
                f"曲线导出功能限制前{download_tightening_results_limit}条数据，将自动截取.或通过设置放大onesphere_wave.download_tightening_results_limit参数"
            )
            records = self[:download_tightening_results_limit]
        _ids = ",".join([str(_id) for _id in records.ids])
        return {
            "type": "ir.actions.act_url",
            "url": f"/oneshare/assembly/tightening/download?ids={_ids}&file_type={file_type}",
            "target": "self",
        }

    def _get_curve_data(self):
        bucket_name = self.env["ir.config_parameter"].get_param("oss.bucket")
        oss_interface = self.env["onesphere.oss.interface"]
        client = oss_interface.ensure_oss_client()
        if not client or not bucket_name:
            return [], None, []  ### 返回无结果数值
        # no_curve_file:结果中没有曲线文件的id，no_minio_result:有曲线文件但是Minio中取不到结果
        no_curve_file, no_minio_result = [], []
        no_curve_file_ids = self.filtered(lambda r: not r.curve_file)
        no_curve_file = no_curve_file_ids.ids
        curve_file_ids = self - no_curve_file_ids
        curve_file = curve_file_ids.ids
        _objects = curve_file_ids.mapped("curve_file")
        entity_id_list = curve_file_ids.mapped("entity_id")
        objects = []
        cur_objects = map(json.loads, _objects)
        objs = list(itertools.chain.from_iterable(cur_objects))
        for cur in objs:
            objects.append(cur["file"])

        need_fetch_objects = []
        _datas, _datas_return = [], []
        for _cur_file in objects:
            try:
                # 尝试从LRU cache中获取数据
                _datas.append(_wave_cache[_cur_file])
            except KeyError as e:
                need_fetch_objects.append(_cur_file)
        try:
            _datas.extend(
                map(
                    lambda curve_file, entity_id: _create_wave_result_dict(
                        entity_id, oss_interface.get_oss_object(bucket_name, curve_file)
                    ),
                    need_fetch_objects,
                    entity_id_list,
                )
            )  # 合并结果
        except Exception as e:
            logger.error(f"Error: {ustr(e)}")
            return []
        for i in range(len(_datas)):
            if not _datas[i]:
                no_minio_result.append(curve_file[i])
                continue
            _datas_return.append(_datas[i])
        return _datas_return, no_curve_file, no_minio_result

    def show_curves(self):
        if not self:
            self.env.user.notify_warning("查询获取结果:0,请重新定义查询参数或等待新结果数据")
            return None, None
        wave_form = self.env.ref("onesphere_wave.spc_compose_wave_wizard_form")
        if not wave_form:
            self.env.user.notify_warning(
                "曲线视图:onesphere_wave.spc_compose_wave_wizard_form 未找到"
            )
            return None, None
        curve_datas, with_no_curvefile, with_no_minio_result = self._get_curve_data()
        if len(with_no_curvefile):
            self.env.user.notify_warning(_("%s have no curve file") % with_no_curvefile)
        if with_no_minio_result:
            self.env.user.notify_warning(
                _("%s have no minio result") % with_no_minio_result
            )
        if not curve_datas:
            # self.env.user.notify_warning(
            #     _('Query Result Data:0,Please Redefine Parameter Of Query or Wait For New Result'))
            return None, None
        curves = json.dumps(curve_datas)
        wave_wizard_id = self.env["wave.compose.wave"].sudo().create({"wave": curves})
        if not wave_wizard_id:
            self.env.user.notify_warning("曲线Wizard视图:wave.compose.wave未找到")
            return None, None
        return wave_form.id, wave_wizard_id.id

    def button_show_curves(self):
        ret1, ret2 = self.show_curves()
        if ret1 and ret2:
            return {
                "name": "Curve Scope",
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_model": "wave.compose.wave",
                "view_id": ret1,
                "res_id": ret2,
                "target": "new",
            }
