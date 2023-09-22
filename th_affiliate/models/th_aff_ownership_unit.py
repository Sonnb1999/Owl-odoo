# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ThCompany(models.Model):
    _inherit = 'res.company'

    th_code_aff = fields.Char('Mã đơn vị sở hữu')
    