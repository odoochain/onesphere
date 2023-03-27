# -*- coding: utf-8 -*-

import logging
from . import controllers
from . import models
from odoo.models import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def create_related_work_station_area_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    workcenters = env["mrp.workcenter"].search([("related_work_area_id", "=", False)])
    for workcenter in workcenters:
        try:
            rec = workcenter.create_related_work_station_area()
            workcenter.write({"related_work_area_id": rec.id})
        except Exception:
            _logger.exception(
                "Create Workcenter[%s] Related Work Station Area Error: %s",
                workcenter.id,
                Exception,
            )
