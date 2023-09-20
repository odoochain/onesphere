import json
import os
import pandas as pd
from jinja2 import Template
import random
import glob
import logging
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, ustr
from script.constants import station_names, attribute_equipments, error_codes

_logger = logging.getLogger(__name__)

DATETIME_LENGTH = len(datetime.today().now().strftime(DEFAULT_SERVER_DATETIME_FORMAT))

DIST_DIR_PATH = "../server/oneshare_enterprise/oneshare_cap_assembly/demo"
DIST_FILE = "tightening_result_demo.xml"

DIST_PATH = "{}/{}".format(DIST_DIR_PATH, DIST_FILE)

RESULT_DATA_PATH = "/home/leext/work/resulta.csv"
FEATURES_PATH = "/home/leext/work/features/*"

TIGHTENING_FEATURES = {
    "曲线唯一标识": "entity_id",
    "测量扭矩": "measure_torque",
    "分段拧紧数量": "step_results",
    "最大扭矩": "max_torque",
    "贴合点扭矩": "snug_torque",
    "终拧紧段扭矩角度序列均方差": "mse_final_tightening",
    "下旋阶段平均扭矩": "rundown_mean_torque",
    "下旋阶段扭矩方差": "rundown_torque_variance",
    "下旋阶段扭矩波峰数量": "rundown_number_of_peaks",
    "下旋阶段扭矩波谷数量": "rundown_number_of_troughs",
    "终拧紧段扭矩波峰数量": "final_number_of_peaks",
    "终拧紧段扭矩波谷数量": "final_number_of_troughs",
    "下旋阶段波峰波谷周期": "rundown_peaks_and_trough_period",
    "终拧紧阶段波峰波谷周期": "final_peaks_and_trough_period",
    "终拧紧段扭矩峰峰值": "final_p_p_values",
    "终拧紧段扭矩角度斜率": "final_toque_div_angle_slope",
}

G_TMPL = Template(
    """
<odoo>
    <data noupdate="1">
        {% for item in items %}
            {{ item }}
        {% endfor %}
        </data>
</odoo>
""",
    autoescape=False,
)

RECORD_TMPL = Template(
    """
        <record id="tightening_result_uat_{{ id }}" model="onesphere.tightening.result">
            <field name="entity_id">{{ entity_id }}</field>
            <field name="track_no">{{ track_no }}</field>
            <field name="tightening_process_no">{{ tightening_process_no }}</field>
            <field name="attribute_equipment_no">{{ attribute_equipment_no }}</field>
            <field name="measurement_final_torque">{{ measurement_final_torque }}</field>
            <field name="measurement_final_angle">{{ measurement_final_angle }}</field>
            <field name="tightening_point_name" ref="{{ tightening_point_name }}"/>
            <field name="step_type">tightening</field>
            <field name="tightening_result">{{ tightening_result }}</field>
            <field name="tightening_strategy">{{ tightening_strategy }}</field>
            <field name="control_time">{{ control_time }}</field>
            <field name="tightening_id">{{ tightening_id }}</field>
            <field name="curve_file">{{ curve_file }}</field>
            <field name="angle_max">{{ angle_max }}</field>
            <field name="angle_min">{{ angle_min }}</field>
            <field name="angle_target">{{ angle_target }}</field>
            <field name="torque_max">{{ torque_max }}</field>
            <field name="error_code">{{ error_code }}</field>
            <field name="torque_min">{{ torque_min }}</field>
            <field name="torque_target">{{ torque_target }}</field>
            <field name="measurement_step_results">{{ step_results }}</field>
            <field name="workcenter_code">{{ workcenter_code }}</field>
            <field name="cap_features_save">{{ cap_features_save }}</field>
            <field name="cap_snug_features_save">{{ cap_snug_features_save }}</field>
            <field name="analysis_result_state">{{ analysis_result_state }}</field>
        </record>
""",
    autoescape=True,
)


def gen_record_msg(*args, **kwargs):
    r = RECORD_TMPL.render(**kwargs)
    return r


def get_step_results(results_str):
    results = json.loads(results_str)
    step_results = []
    for result in results:
        step_result = []
        for dim in ["torque", "angle"]:
            step_result.append(
                {
                    "dimension": dim,
                    "value": round(result.get(f"measure_{dim}", 0.0), 2),
                    "spec": {
                        "max": round(result.get(f"{dim}_max", 0.0), 2),
                        "min": round(result.get(f"{dim}_min", 0.0), 2),
                        "threshold": round(result.get(f"{dim}_threshold", 0.0), 2),
                        "target": round(result.get(f"{dim}_target", 0.0), 2),
                    },
                }
            )
        step_results.append(step_result)
    return step_results


def get_feature_df():
    feature = False
    for file in glob.glob(FEATURES_PATH):
        feature_df_item = pd.read_excel(file)
        if feature is not False:
            feature = pd.concat([feature, feature_df_item], ignore_index=True)
        else:
            feature = feature_df_item
    feature.set_index("曲线唯一标识", inplace=True)
    feature.drop("人为识别拧紧结果", axis="columns", inplace=True)
    feature.rename(columns=TIGHTENING_FEATURES, inplace=True)
    return feature


def get_feature_json(entity):
    feature, snug = "", ""
    try:
        feature_item = json.loads(feature_df.loc[entity].to_json())
        feature_item.update(
            {"step_results": len(json.loads(feature_item.get("step_results")))}
        )
        snug = feature_item.pop("snug_data", "")
        feature_dic = {data["entity_id"][index]: feature_item}
        feature = json.dumps(feature_dic, indent=4)
    except Exception as e:
        _logger.error("get feature json failed: %s", ustr(e))
    return feature, snug


if __name__ == "__main__":
    if os.path.exists(DIST_PATH):
        os.remove(DIST_PATH)
    rec_str = []
    feature_df = get_feature_df()
    data = pd.read_csv(RESULT_DATA_PATH).to_dict()
    for index in range(len(data.get("pk"))):
        track_no = data["vin"][index][:8]
        tightening_process_no = data["pset"][index]
        measurement_final_torque = data["measure_torque"][index]
        measurement_final_angle = data["measure_angle"][index]
        tightening_point_name = f"{data['nut_no'][index]}-1"
        tightening_point_name = tightening_point_name.replace("OP340-", "OP340_")
        tightening_point_name = tightening_point_name.replace("-0-0", "-1-1")
        tightening_result = data["measure_result"][index].lower()
        error_code = random.choice(error_codes) if tightening_result == "nok" else ""
        tightening_strategy = random.choice(["AD", "AW"])
        control_time = (
            data["update_time"][index][:DATETIME_LENGTH]
            if data["update_time"][index]
            else datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        )
        control_timestamp = int(
            datetime.strptime(control_time, DEFAULT_SERVER_DATETIME_FORMAT).timestamp()
        )
        if tightening_point_name in (
            "OP340_8-1-1-1",
            "OP940-1-1-1",
            "OP340_6-1-1-1",
            "OP800-1-1-1",
        ):
            angle_max, angle_min, angle_target = 100, 0, 50
        elif tightening_point_name in ("OP1000-1-1-1", "OP1050-1-1-1"):
            angle_max, angle_min, angle_target = 200, 0, 100
        elif tightening_point_name == "H170-1-1-1":
            angle_max, angle_min, angle_target = 1000, 0, 500
        elif tightening_point_name == "OP1470-1-1-1":
            angle_max, angle_min, angle_target = 800, 0, 400
        else:
            angle_max = data["angle_max"][index]
            angle_min = data["angle_min"][index]
            angle_target = data["angle_target"][index]
        entity_id = f"{track_no}_{data['tool_sn'][index]}_{control_timestamp}_{index}"
        tightening_id = data["tightening_id"][index]
        curve = f"{data['entity_id'][index].split('/')[-1]}.json"
        curve_file = '[{"file":"%s","op":1}]' % curve
        torque_max = data["torque_max"][index]
        torque_min = data["torque_min"][index]
        torque_target = data["torque_target"][index]
        analysis_result_state = "ok" if tightening_result == "ok" else "nok"
        if curve in ("1644116132.json", "1644114233.json"):
            analysis_result_state = "nok"
        step_results = json.dumps(get_step_results(data["step_results"][index]))
        workcenter_code = random.choice(station_names)
        attribute_equipment_no = random.choice(attribute_equipments)
        feature_json, snug_data = get_feature_json(data["entity_id"][index])
        m = gen_record_msg(
            id=index,
            entity_id=entity_id,
            track_no=track_no,
            tightening_process_no=tightening_process_no,
            measurement_final_torque=measurement_final_torque,
            measurement_final_angle=measurement_final_angle,
            tightening_point_name=tightening_point_name,
            tightening_result=tightening_result,
            error_code=error_code,
            tightening_strategy=tightening_strategy,
            control_time=control_time,
            tightening_id=tightening_id,
            curve_file=curve_file,
            angle_max=angle_max,
            angle_min=angle_min,
            angle_target=angle_target,
            torque_max=torque_max,
            torque_min=torque_min,
            torque_target=torque_target,
            step_results=step_results,
            workcenter_code=workcenter_code,
            attribute_equipment_no=attribute_equipment_no,
            cap_features_save=feature_json,
            cap_snug_features_save=snug_data,
            analysis_result_state=analysis_result_state,
        )
        rec_str.append(m)
    ss = G_TMPL.render(items=rec_str)
    with open(DIST_PATH, "w") as f:
        f.write(ss)
