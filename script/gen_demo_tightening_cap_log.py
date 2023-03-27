# -*- coding: utf-8 -*-
import os
import random

from faker import Faker
from jinja2 import Template

fake = Faker()

DIST_RESULT_DIR_PATH = "../server/onesphere/onesphere_assembly_industry/demo"
DIST_RESULT_FILE = "tightening_result_demo.xml"

DIST_RESULT_PATH = "{}/{}".format(DIST_RESULT_DIR_PATH, DIST_RESULT_FILE)

DIST_DIR_PATH = "../server/oneshare_enterprise/oneshare_cap_assembly/demo"
DIST_FILE = "cap_analysis_log_demo.xml"

DIST_PATH = "{}/{}".format(DIST_DIR_PATH, DIST_FILE)

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
    autoescape=True,
)

RECORD_TMPL = Template(
    """
        <record id="onesphere_assembly_industry.tightening_result_{{ id }}"  model="onesphere.tightening.result">
            <field name="analysis_result_state">{{ analysis_result_state }}</field>
            <field name="final_judge_analysis_result_state">{{ analysis_result_state }}</field>
            <field name="cap_error_massage">{{ cap_error_massage }}</field>
        </record>
""",
    autoescape=True,
)


def gen_record_msg(*args, **kwargs):
    r = RECORD_TMPL.render(**kwargs)
    return r


from typing import List, Dict


def convert_fields_to_dict(fields: List) -> Dict:
    field: Dict = {}
    ret = {}
    for field in fields:
        key = field.pop("@name")
        ret[key] = field
    return ret


if __name__ == "__main__":
    if os.path.exists(DIST_PATH):
        os.remove(DIST_PATH)
    rec_str = []
    result_dict = {}
    # with open(DIST_RESULT_PATH) as f:
    #     a = f.read()
    #     result_dict = xmltodict.parse(a)
    # results = result_dict.get('odoo', {}).get('data', {}).get('record', [])
    for i in range(1000):
        delta_day = random.choice([1, 2])
        analysis_result_state = random.choice(["ok", "nok"])
        cap_error_massage = random.choice(["", "101", "101,102", "101,102,103"])
        if analysis_result_state == "ok":
            cap_error_massage = ""
        m = gen_record_msg(
            id=i,
            analysis_result_state=analysis_result_state,
            cap_error_massage=cap_error_massage,
        )
        rec_str.append(m)
    ss = G_TMPL.render(items=rec_str)
    with open(DIST_PATH, "w") as f:
        f.write(ss)
