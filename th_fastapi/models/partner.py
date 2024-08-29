from odoo import api, fields
from odoo.models import BaseModel


class Partner(BaseModel):
    _inherit = 'res.partner'

    th_phone2 = fields.Char(string='Phone2')
    @api.model
    def th_get_partner(self, datas):
        partner = self.sudo().search([])
        return partner

    def th_create_partner(self, datas):
        domain = [
            '|', '|', ('phone', '=', datas.get('phone')), ('th_phone2', '=', datas.get('phone')),
            '|', '|', ('phone', '=', datas.get('phone2', '  ')),
            ('th_phone2', '=', datas.get('phone2', '  ')),
            ('email', '=', datas.get('email', '  '))
        ]
        partner = self.sudo().search(domain, limit=1)
        if not partner:
            partner = super(Partner, self).create(datas)
        return partner

    def th_update_partner(self, datas):
        th_id = int(datas.get('id'))
        datas.pop('id')
        partner = self.browse(int(th_id)).exists().sudo().write(datas)
        return partner

    def th_unlink_partner(self, datas):
        return self.browse(int(datas.get('id'))).exists().sudo().unlink()

