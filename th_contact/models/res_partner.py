from odoo import fields, models, api, _
import xmlrpc.client

url, db, username, password = 'http://10.10.50.130:8016/', 'base', 'admin', '6bb74aaaae2a0d81b141d4a1bdcfe23f06bd146e'


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

    th_bank = fields.Char(string="Ngân hàng", tracking=True)
    th_account_name = fields.Char(string="Tên tài khoản", tracking=True)
    th_account_number = fields.Char(string="Số tài khoản", tracking=True)
    th_account_branch = fields.Char(string="Chi nhánh", tracking=True)
    th_tax_no = fields.Char(string="Mã số thuế", tracking=True)
    th_pom_id = fields.Char('Contact')

    def update_bank(self):
        pass

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
        th_customer_code = values.get('th_affiliate_code', False)
        if not th_customer_code and values.get('th_pom_id'):
            values['th_customer_code'] = self.env['ir.sequence'].next_by_code('customer.code')
            values['th_affiliate_code'] = self.env['ir.sequence'].next_by_code('affiliate.code')

        return super(ResPartner, self).create(values)
