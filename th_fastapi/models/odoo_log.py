# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class OdooLog(models.Model):
    _name = 'th.odoo.log'

    name = fields.Char(string='Name', required=False)
    th_data = fields.Text(string='Data', required=False)
    th_method = fields.Selection(selection=[('GET', 'GET'), ('POST', 'POST'), ('UPDATE', 'UPDATE'), ('DELETE', 'DELETE')],
                              string='Method')
    th_type = fields.Selection(selection=[('instant', 'Instant'), ('hour', '1 hour 1 time'), ('24hours', '24 hours 1 time')])

    @api.model
    def create(self, values):
        return super(OdooLog, self).create(values)
