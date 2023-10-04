from odoo import fields, models, api, _
from odoo import exceptions


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _th_domain_place_of_birth(self):
        state_id = self.env['res.country.state'].search([]).filtered(lambda u: u.country_id == self.env.ref('base.vn'))
        return [('id', 'in', state_id.ids)]


    country_id = fields.Many2one('res.country', default=lambda x: x.env.ref('base.vn'))
    th_ward_id = fields.Many2one(comodel_name='th.country.ward', string='Phường/ Xã', domain="[('th_district_id', '=?', th_district_id), ('th_district_id.th_state_id', '=?', state_id)]", tracking=True)
    th_district_id = fields.Many2one(comodel_name='th.country.district', string='Quận/ Huyện', domain="[('th_state_id', '=?', state_id)]", tracking=True)

    th_customer_code = fields.Char(string="Mã Khách Hàng", readonly=True, tracking=True)
    th_affiliate_code = fields.Char(string="Mã Tiếp Thị Liên Kết", readonly=True, tracking=True)

    th_gender = fields.Selection(string="Giới tính", selection=[('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác'), ], tracking=True)
    th_birthday = fields.Date(string="Ngày sinh", tracking=True)
    th_place_of_birth_id = fields.Many2one(comodel_name="res.country.state", string="Nơi sinh", domain=_th_domain_place_of_birth)
    th_phone2 = fields.Char(string="Số điện thoại 2", tracking=True)
    th_citizen_identification = fields.Char(string="Số CMT/ CCCD", tracking=True)
    th_date_identification = fields.Date(string="Ngày cấp CMT/ CCCD", tracking=True)
    th_place_identification = fields.Char(string="Nơi cấp CMT/ CCCD", tracking=True)

    @api.onchange('th_ward_id')
    def onchange_th_ward_id(self):
        if self.th_ward_id:
            self.th_district_id = self.th_ward_id.th_district_id.id
            self.state_id = self.th_district_id.th_state_id.id
            self.country_id = self.state_id.country_id.id

    @api.onchange('th_district_id')
    def onchange_th_district_id(self):
        if self.th_district_id:
            self.state_id = self.th_district_id.th_state_id.id
            self.country_id = self.state_id.country_id.id
        if self.th_district_id != self.th_ward_id.th_district_id:
            self.th_ward_id = False

    @api.onchange('country_id')
    def onchange_th_country_id(self):
        if self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def onchange_th_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id
        if self.state_id != self.th_district_id.th_state_id:
            self.th_district_id = False

    @api.model
    def create(self, values):
        if 'th_customer_code' not in values or 'th_customer_code' not in values:
            values['th_customer_code'] = self.env['ir.sequence'].next_by_code('customer.code')
            values['th_affiliate_code'] = self.env['ir.sequence'].next_by_code('affiliate.code')
        return super(ResPartner, self).create(values)
