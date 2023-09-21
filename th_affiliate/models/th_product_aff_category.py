from odoo import tools, models, fields, api, _
from collections import defaultdict

from odoo.exceptions import ValidationError

URL_MAX_SIZE = 10 * 1024 * 1024


class ThProductAffCategory(models.Model):
    _name = 'th.product.aff.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "th_category_parent_id"
    _parent_store = True
    _rec_name = 'th_complete_name'
    _order = 'th_complete_name'

    name = fields.Char("Tên nhóm", index='trigram', required=True)
    th_category_parent_id = fields.Many2one('th.product.aff.category', 'Nhóm cha', index=True, ondelete='cascade', domain="[('id', '!=', id)]")
    th_complete_name = fields.Char('Complete Name', compute='_compute_th_complete_name', recursive=True, store=True)
    parent_path = fields.Char(index=True, unaccent=False)
    th_child_id = fields.One2many('th.product.aff.category', 'th_category_parent_id', 'Child Categories')

    @api.onchange('name')
    def onchange_name_category(self):
        for rec in self:
            search_name = self.sudo().search([('name', '=', rec.name)])
            if search_name and not rec.ids:
                raise ValidationError("The category name already exists!")
            rec.name = rec.name

    @api.depends('name', 'th_category_parent_id.th_complete_name')
    def _compute_th_complete_name(self):
        for category in self:
            if category.th_category_parent_id:
                category.th_complete_name = '%s / %s' % (category.th_category_parent_id.th_complete_name, category.name)
            else:
                category.th_complete_name = category.name


class ThProductAff(models.Model):
    _name = 'th.product.aff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char("Tên sản phẩm", index='trigram', required=True, tracking=True)
    th_link_product = fields.Char('Link sản phẩm', required=True, tracking=True)
    th_image = fields.Image(string="image")
    th_aff_category_id = fields.Many2one('th.product.aff.category', 'Nhóm sản phẩm', required=True, tracking=True)
    # th_aff_ownership_unit_id = fields.Many2one('th.aff.ownership.unit', 'Đơn vị sở hữu', tracking=True, required=1)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('deploy', 'Triển khai'),
            ('close', 'Đóng'),
        ],
        string='Status',
        required=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    def action_visit_page(self):
        return {
            'name': _("Xem link"),
            'type': 'ir.actions.act_url',
            'url': self.th_link_product,
            'target': 'new',
        }

    def action_draft(self):
        self.write({
            'state': 'draft'
        })

    def action_deploy(self):
        self.write({
            'state': 'deploy'
        })

    def action_close(self):
        self.write({
            'state': 'close'
        })

    # @api.model
    # def create(self, values):
    #     th_user_id = self.env.user
    #     if not values.get('th_aff_ownership_unit_id', False) and th_user_id.th_aff_team:
    #         values['th_aff_ownership_unit_id'] = th_user_id.th_aff_team.id
    #     return super(ThProductAff, self).create(values)
