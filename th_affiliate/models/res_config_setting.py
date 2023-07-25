# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

_interval_selection = {'minutes': 'Minutes', 'hours': 'Hours', 'days': 'Days'}
_interval_types = {
    'minutes': lambda interval: relativedelta(minutes=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'days': lambda interval: relativedelta(days=interval),
}

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    th_access_interval_number = fields.Integer(default=7, tracking=True, help="")
    th_access_interval_type = fields.Selection(list(_interval_selection.items()), default='days', tracking=True)
