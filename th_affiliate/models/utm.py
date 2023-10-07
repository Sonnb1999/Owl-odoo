# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class UtmCampaign(models.Model):
    _inherit = 'utm.campaign'

    th_start_date = fields.Date('Ngày bắt đầu', required=True)
    th_end_date = fields.Date('Ngày kết thúc', required=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
