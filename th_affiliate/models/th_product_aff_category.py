from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024


class ThProductAffCategory(models.Model):
    _name = 'th.product.aff.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'th_complete_name'
    _order = 'th_complete_name'

    name = fields.Char("Tên nhóm", index='trigram', required=True)
    parent_id = fields.Many2one('th.product.aff.category', 'Nhóm cha', index=True, ondelete='cascade')
    th_complete_name = fields.Char('Complete Name', compute='_compute_th_complete_name', recursive=True, store=True)
    parent_path = fields.Char(index=True, unaccent=False)
    child_id = fields.One2many('th.product.aff.category', 'parent_id', 'Child Categories')

    @api.depends('name', 'parent_id.th_complete_name')
    def _compute_th_complete_name(self):
        for category in self:
            if category.parent_id:
                category.th_complete_name = '%s / %s' % (category.parent_id.th_complete_name, category.name)
            else:
                category.th_complete_name = category.name


class ThProductAff(models.Model):
    _name = 'th.product.aff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char("Tên sản phẩm", index='trigram', required=True)
    th_link_product = fields.Char('Link sản phẩm', required=True, tracking=True)
    th_image = fields.Image(string="image")
    th_aff_category_id = fields.Many2one('th.product.aff.category', 'Nhóm sản phẩm', required=True)
    th_aff_ownership_unit_id = fields.Many2one('th.aff.ownership.unit', 'Đơn vị sở hữu', tracking=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('active', 'Triển khai'),
            ('inactive', 'Đóng'),
        ],
        string='Status',
        required=True,
        copy=False,
        tracking=True,
        default='draft',
    )
