from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'th.pay'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # partner_id = ''