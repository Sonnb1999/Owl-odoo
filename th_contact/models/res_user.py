from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import xmlrpc.client

url, db, username, password = 'http://10.10.50.130:8016/', 'base_aff', 'admin', '6bb74aaaae2a0d81b141d4a1bdcfe23f06bd146e'


class ResUsers(models.Model):
    _inherit = "res.users"
    _description = "user"

    @api.model
    def create(self, values):
        res_values = {}
        email = values.get('email', False) or values.get('login', False)
        if not email:
            raise ValidationError("Không có email login!")
        if values.get('th_pom_id', False):
            res_partner = self.env['res.partner'].sudo().create(values)
            res_values = {
                'name': values['name'],
                'login': email,
                'partner_id': res_partner.id if res_partner else False
            }
        user = super(ResUsers, self).create(res_values or values)
        self.action_reset_password()

        return user
