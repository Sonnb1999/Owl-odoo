from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    th_url_server = fields.Char('URL server')
    th_user = fields.Char('Tài khoản sử dụng API')
    th_password = fields.Char('Key API')
    th_db = fields.Char('DataBase')

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].set_param('th_url_server', self.th_url_server)
        self.env['ir.config_parameter'].set_param('th_user', self.th_user)
        self.env['ir.config_parameter'].set_param('th_password', self.th_password)
        self.env['ir.config_parameter'].set_param('th_db', self.th_db)

    @api.model
    def get_values(self):
        res = super().get_values()
        th_url_server = self.env['ir.config_parameter'].get_param('th_url_server', self.th_url_server)
        th_user = self.env['ir.config_parameter'].get_param('th_user', self.th_user)
        th_password = self.env['ir.config_parameter'].get_param('th_password', self.th_password)
        th_db = self.env['ir.config_parameter'].get_param('th_db', self.th_db)

        res.update(th_url_server=th_url_server,
                   th_user=th_user,
                   th_password=th_password,
                   th_db=th_db
                   )
        return res
