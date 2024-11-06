# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class OdooIn(models.Model):
    _name = 'th.odoo.inherit'

    def check_function(self):
        print(self.env['ir.model.data'])
