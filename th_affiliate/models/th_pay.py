from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'th.pay'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    th_partner_id = fields.Many2one('res.partner', string="Cộng tác viên")
    th_post_link_ids = fields.One2many('th.post.link', 'th_pay_id', 'Post link')
    state = fields.Selection(selection=[('draft', 'Chờ duyệt'), ('accept', 'Duyệt'), ('paid', 'Đã Thanh toán')])
    th_count_link = fields.Integer('Số bài đăng', default=0)
    th_payed = fields.Char('Tổng')
