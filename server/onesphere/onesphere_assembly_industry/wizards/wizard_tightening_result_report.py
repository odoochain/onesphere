from itertools import zip_longest
from typing import Union

import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Pie
from snapshot_phantomjs import snapshot

from odoo import fields, models, _
from odoo.exceptions import ValidationError


def generate_base64_image_content_str(chart):
    img_data = snapshot.make_snapshot(
        html_path=chart.render(),
        file_type="png",
        delay=1,
        pixel_ratio=2,
    )  # base64 string

    content = img_data.replace(
        "TypeError: Attempting to change the setter of an unconfigurable property.", ""
    )
    return content


def generate_pie_chart(title, subtitle, pairs):
    c = (
        Pie(
            init_opts=opts.InitOpts(width="1000px", height="625px"),
        )
        .add(
            title,
            pairs,
            radius=["30%", "45%"],
            label_opts=opts.LabelOpts(
                position="outside",
                formatter="{a|{a}}{abg|}\n{hr|}\n {b|{b}: }{c|{c}}  {per|{d}%}  ",
                font_size=36,
                background_color="#eee",
                border_color="#aaa",
                border_width=1,
                border_radius=4,
                rich={
                    "a": {
                        "color": "#86909c",
                        "lineHeight": 40,
                        "fontSize": 26,
                        "align": "center",
                    },
                    "abg": {
                        "backgroundColor": "#e3e3e3",
                        "width": "100%",
                        "align": "right",
                        "height": 50,
                        "borderRadius": [4, 4, 0, 0],
                    },
                    "hr": {
                        "borderColor": "#c9cdd4",
                        "width": "100%",
                        "borderWidth": 0.5,
                        "height": 0,
                    },
                    "b": {"fontSize": 24, "fontWeight": "bold", "lineHeight": 33},
                    "c": {"fontSize": 24, "lineHeight": 33},
                    "per": {
                        "color": "#eee",
                        "fontSize": 24,
                        "backgroundColor": "#4e5969",
                        "padding": [2, 4],
                        "borderRadius": 2,
                    },
                },
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title=subtitle, title_textstyle_opts=opts.TextStyleOpts(font_size=24)
            ),
            legend_opts=opts.LegendOpts(
                pos_right="15%",
                textstyle_opts=opts.TextStyleOpts(font_size=24),
            ),
        )
    )
    return c


def get_pie_label_value_color_pair(labels, values):
    colors = ["#4CD263", "#F53F3F"]

    pairs = []
    for label, value, color in zip_longest(
        labels, values, colors[: len(labels)], fillvalue="#86909c"
    ):
        pairs.append(
            opts.PieItem(
                name=label, value=value, itemstyle_opts=opts.ItemStyleOpts(color=color)
            )
        )
    return pairs


def statistic_pie_chart(
    group_by, final_ok_count=0, bolt_count=0, final_ok_percent="0.0%"
):
    show_string = {
        "bolt_no": "螺栓编号合格率",
        "work_center": "工位编号合格率",
    }
    labels = ["最终合格数量", "最终不合格数量"]
    values = [final_ok_count, bolt_count - final_ok_count]

    pairs = get_pie_label_value_color_pair(labels, values)

    c = generate_pie_chart(
        show_string.get(group_by, "编号合格率"), f"最终合格率: {final_ok_percent}", pairs=pairs
    )

    content = generate_base64_image_content_str(c)
    return content


def result_statistic_pie_chart(results_pd, abnormal_percent):
    labels = list(map(str.upper, results_pd.index.tolist()))
    values = results_pd["count"].tolist()

    pairs = get_pie_label_value_color_pair(labels, values)

    c = generate_pie_chart("拧紧合格异常比例", f"拧紧合格异常比例: {abnormal_percent}", pairs)

    content = generate_base64_image_content_str(c)

    return content


def calculate_percent(
    numerator: Union[float, int], denominator: Union[float, int], float_num: int
):
    return f"{round(numerator * 100 / denominator, float_num)}%"


class WizardTighteningResultReport(models.TransientModel):
    _name = "wizard.tightening.result.report"
    _description = "Wizard Tightening Result Report"

    track_no = fields.Char(string="Track No", required=True)
    group_by = fields.Selection(
        [
            ("bolt_no", "Bolt_No"),
            ("work_center", "Work_Center"),
        ],
        default="bolt_no",
        string="group by",
        required=True,
    )

    def get_tightening_point(self):
        sql = f""" SELECT distinct(tightening_point_name) from onesphere_tightening_result WHERE track_no='{self.track_no}' """
        self._cr.execute(sql)
        results = self._cr.fetchall()
        return results

    def get_work_center(self):
        sql = f""" SELECT distinct(workcenter_code) from onesphere_tightening_result WHERE track_no='{self.track_no}' """
        self._cr.execute(sql)
        results = self._cr.fetchall()
        return results

    def get_results_via_work_center(self, work_center):
        work_center_query = f"""'workcenter_code = '{work_center}' """
        if not work_center:
            work_center_query = "workcenter_code is Null"

        sql = f"""SELECT tightening_result, tightening_process_no, measurement_final_torque, measurement_final_angle, 
                control_time, otb.name, attribute_equipment_no, error_code FROM onesphere_tightening_result 
                             left join onesphere_tightening_bolt otb on otb.id = onesphere_tightening_result.tightening_point_name
                WHERE track_no='{self.track_no}' AND  {work_center_query}  ORDER BY tightening_point_name, control_time"""
        self._cr.execute(sql)
        results = self._cr.fetchall()

        sql2 = f"""SELECT tightening_result from 
                (select t.*,row_number() over(partition by tightening_point_name order by control_time desc) rn
                from onesphere_tightening_result t 
                WHERE track_no='{self.track_no}' AND  {work_center_query} ) a  where a.rn = 1    
        """
        self._cr.execute(sql2)
        last_results = self._cr.fetchall()
        final_result = (
            "ok" if all(result[0] == "ok" for result in last_results) else "nok"
        )
        return results, final_result

    def get_count_groupby_tightening_result(self, filter="1=1"):
        sql = f"""SELECT tightening_result, count(*) FROM onesphere_tightening_result WHERE track_no='{self.track_no}' AND {filter} GROUP BY tightening_result ORDER BY tightening_result desc"""
        self._cr.execute(sql)
        d = self._cr.fetchall()
        result = {dd[0]: dd[1] for dd in d}
        return result

    def get_results_via_blot_id(self, bolt_id):
        sql = f"""SELECT tightening_result, tightening_process_no, measurement_final_torque, measurement_final_angle, 
                control_time, workcenter_code, attribute_equipment_no, error_code FROM onesphere_tightening_result 
                WHERE track_no='{self.track_no}' AND tightening_point_name={bolt_id} ORDER BY control_time"""
        self._cr.execute(sql)
        results = self._cr.fetchall()
        return results

    def get_bolt_number(self, bolt_id):
        sql = f"""SELECT name from onesphere_tightening_bolt WHERE id={bolt_id} """
        self._cr.execute(sql)
        result = self._cr.fetchone()
        return result[0]

    def get_results_group_by_bolt(self, tightening_point_list):
        tightening_results = []
        first_ok_count, final_ok_count = 0, 0
        for bolt in tightening_point_list:
            bolt_id = bolt[0]
            bolt_name = self.get_bolt_number(bolt_id)
            results_of_bolt = self.get_results_via_blot_id(bolt_id)
            tightening_results.append(
                {
                    "bolt_id": bolt_id,
                    "name": bolt_name if bolt_name else "未知",
                    "results": results_of_bolt,
                    "count": len(results_of_bolt),
                    "final_result": results_of_bolt[-1][0],
                }
            )
            if results_of_bolt[0][0] == "ok":
                first_ok_count += 1
            if results_of_bolt[-1][0] == "ok":
                final_ok_count += 1
        return tightening_results, first_ok_count, final_ok_count

    def get_results_group_by_work_center(self, work_center_list):
        tightening_results = []
        final_ok_count = 0
        for work_center in work_center_list:
            results_of_work_center, final_result = self.get_results_via_work_center(
                work_center[0]
            )
            tightening_results.append(
                {
                    "name": work_center[0] if work_center[0] else "未知",
                    "results": results_of_work_center,
                    "count": len(results_of_work_center),
                    "final_result": final_result,
                }
            )
            if final_result == "ok":
                final_ok_count += 1
        return tightening_results, final_ok_count

    def get_report_data(self):
        results = self.get_count_groupby_tightening_result()
        results_pd = pd.DataFrame.from_dict(results, orient="index", columns=["count"])
        result_count = results_pd["count"].sum()
        if result_count < 1:
            raise ValidationError(_("No result record!"))
        ok_count = results_pd.loc["ok"]["count"]
        abnormal_count = result_count - ok_count
        ok_percent = calculate_percent(ok_count, result_count, 2)
        abnormal_percent = calculate_percent(abnormal_count, result_count, 2)
        results_group_by = []
        first_ok_count, final_ok_count, sum_count = 0, 0, 0
        if self.group_by == "bolt_no":
            tightening_point_list = self.get_tightening_point()
            sum_count = len(tightening_point_list)
            (
                results_group_by,
                first_ok_count,
                final_ok_count,
            ) = self.get_results_group_by_bolt(tightening_point_list)
        if self.group_by == "work_center":
            work_center_list = self.get_work_center()
            sum_count = len(work_center_list)
            results_group_by, final_ok_count = self.get_results_group_by_work_center(
                work_center_list
            )

        first_ok_percent = calculate_percent(first_ok_count, sum_count, 2)
        final_ok_percent = calculate_percent(final_ok_count, sum_count, 2)
        data = {
            "group_by": self.group_by,
            "track_no": self.track_no,
            "count": result_count,
            "ok_count": ok_count,
            "abnormal_count": abnormal_count,
            "ok_percent": ok_percent,
            "abnormal_percent": abnormal_percent,
            "sum_count": sum_count,
            "first_ok_count": first_ok_count,
            "final_ok_count": final_ok_count,
            "first_ok_percent": first_ok_percent,
            "final_ok_percent": final_ok_percent,
            "results": results_group_by,
            "bolt_statistic_pie_chart": statistic_pie_chart(
                self.group_by, final_ok_count, sum_count, final_ok_percent
            ),
            "result_statistic_pie_chart": result_statistic_pie_chart(
                results_pd, abnormal_percent
            ),
        }
        return data

    def print_report(self):
        self.ensure_one()
        data = self.get_report_data()
        report = self.env.ref(
            "onesphere_assembly_industry.print_tightening_result_report"
        )
        return report.report_action([], data=data)
