# -*- coding: utf-8 -*-
import os
import random
import uuid

from faker import Faker
from jinja2 import Template

from script.constants import track_codes, tightening_bolts, attribute_equipments

fake = Faker()

DIST_DIR_PATH = "../server/onesphere/onesphere_assembly_industry/demo"
DIST_FILE = "tightening_result_demo.xml"

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
""", autoescape=True
)

RECORD_TMPL = Template(
    """
        <record id="tightening_result_{{ id }}" model="onesphere.tightening.result">
            <field name="entity_id">{{ entity_id }}</field>
            <field name="track_no">{{ track_no }}</field>
            <field name="attribute_equipment_no">{{ attribute_equipment_no }}</field>
            <field name="measurement_final_torque">{{ torque }}</field>
            <field name="measurement_final_angle">{{ degree }}</field>
            <field name="step_type">tightening</field>
            <field name="tightening_process_no">{{ tightening_process_no }}</field>
            <field name="tightening_point_name" ref="{{ tightening_bolt_id }}"/>
            <field name="tightening_result">{{ result }}</field>
            <field name="tightening_strategy">{{ tightening_strategy }}</field>
            <field name="control_time" eval="(DateTime.today() - relativedelta(days={{ delta_day }})).strftime('%Y-%m-%d %H:%M')"/>
            <field name="tightening_id">{{ tightening_id }}</field>
        </record>
""", autoescape=True
)


def gen_record_msg(*args, **kwargs):
    r = RECORD_TMPL.render(**kwargs)
    return r


def random_track_codes():
    return [lambda d: fake.ean13() for d in range(5)]


if __name__ == "__main__":
    if os.path.exists(DIST_PATH):
        os.remove(DIST_PATH)
    rec_str = []
    # track_codes = random_track_codes()
    for i in range(1000):
        torque = round(random.uniform(3.5, 5.4), 2)
        degree = round(random.uniform(165.5, 187.5), 2)
        result = random.choice(["ok", "nok", "ak2"])
        tightening_strategy = random.choice(["AD", "AW"])
        tightening_process_no = random.choice(["1", "2", "3"])
        delta_day = random.randint(1, 20)
        track_no = random.choice(track_codes)
        attribute_equipment_no = random.choice(attribute_equipments)
        tightening_bolt_id = random.choice(tightening_bolts)
        m = gen_record_msg(
            entity_id=str(uuid.uuid4()),
            id=i,
            attribute_equipment_no=attribute_equipment_no,
            track_no=track_no,
            torque=torque,
            degree=degree,
            result=result,
            tightening_bolt_id=tightening_bolt_id,
            tightening_strategy=tightening_strategy,
            tightening_process_no=tightening_process_no,
            delta_day=delta_day,
            tightening_id=i + 1,
        )
        rec_str.append(m)
    ss = G_TMPL.render(items=rec_str)
    with open(DIST_PATH, "w") as f:
        f.write(ss)
