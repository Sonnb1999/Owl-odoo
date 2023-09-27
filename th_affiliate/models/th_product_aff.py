from odoo import models, fields, _

state_acceptance = [('draft', 'Nháp'), ('deploy', 'Triển khai'), ('close', 'Đóng')]


class ThProductAff(models.Model):
    _name = 'th.product.aff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char("Tên sản phẩm", index='trigram', required=True, tracking=True)
    th_link_product = fields.Char('Link sản phẩm', required=True, tracking=True)
    th_image = fields.Image(string="image")
    th_aff_category_id = fields.Many2one('th.product.aff.category', 'Nhóm sản phẩm', required=True, tracking=True, check_company=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state = fields.Selection(selection=state_acceptance, string='Status', required=True, copy=False, tracking=True, default='draft')

    def action_visit_page(self):
        return {
            'name': _("Xem link"),
            'type': 'ir.actions.act_url',
            'url': self.th_link_product,
            'target': 'new',
        }

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_deploy(self):
        self.write({'state': 'deploy'})

    def action_close(self):
        self.write({'state': 'close'})

