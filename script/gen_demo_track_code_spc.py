# -*- coding: utf-8 -*-
import os
from jinja2 import Template
from script.constants import track_codes
from faker import Faker

fake = Faker()

DIST_DIR_PATH = "../server/onesphere/onesphere_core/demo"
DIST_FILE = "track_code_demo.xml"

DIST_PATH = "{}/{}".format(DIST_DIR_PATH, DIST_FILE)

G_TMPL = Template(
    """
<odoo>
    <data noupdate="0">
        {% for item in items %}
            {{ item }}
        {% endfor %}
        </data>
</odoo>
""", autoescape=True
)

RECORD_TMPL = Template(
    """
        <record id="track_code_{{ id }}" model="oneshare.track.code">
            <field name="track_code">{{ track_no }}</field>
        </record>
""", autoescape=True
)


def gen_record_msg(*args, **kwargs):
    r = RECORD_TMPL.render(**kwargs)
    return r


if __name__ == "__main__":
    if os.path.exists(DIST_PATH):
        os.remove(DIST_PATH)
    rec_str = []
    for i, track_no in enumerate(track_codes):
        m = gen_record_msg(id=i, track_no=track_no)
        rec_str.append(m)
    ss = G_TMPL.render(items=rec_str)
    with open(DIST_PATH, "w") as f:
        f.write(ss)
