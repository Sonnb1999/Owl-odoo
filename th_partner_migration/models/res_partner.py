# Copyright Nova Code (http://www.novacode.nl)
# See LICENSE file for full licensing details.

from odoo import api, fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    th_name_extra = fields.Char(string='Extra Name')
    th_user_id = fields.Many2one('res.users', string='Related User', ondelete='set null')