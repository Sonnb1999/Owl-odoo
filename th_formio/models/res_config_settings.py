from odoo import fields, models, api


class ThResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    th_form_manager_ids = fields.Many2many('res.users', string='Người duyệt form')

    # Override get_values to retrieve the th_form_manager_ids from ir.config_parameter
    @api.model
    def get_values(self):
        res = super().get_values()
        th_form_manager_ids = self.env['ir.config_parameter'].sudo().get_param('th_form_manager_ids')
        if th_form_manager_ids:
            res.update({
                'th_form_manager_ids': [(6, 0, eval(th_form_manager_ids))]
            })
        return res

    # Override set_values to save the th_form_manager_ids
    def set_values(self):
        super().set_values()
        th_form_manager_ids = self.th_form_manager_ids.ids
        self.env['ir.config_parameter'].sudo().set_param('th_form_manager_ids', str(th_form_manager_ids))
