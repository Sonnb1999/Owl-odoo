from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    th_url_server = fields.Char('URL server')
    th_user = fields.Char('Tài khoản sử dụng API')
    th_password = fields.Char('Key API')
    th_db = fields.Char('DataBase')


