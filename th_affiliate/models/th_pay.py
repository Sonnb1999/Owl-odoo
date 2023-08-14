from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'th.pay'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'th_partner_id'

    th_partner_id = fields.Many2one('res.partner', string="Cộng tác viên")
    th_post_link_ids = fields.One2many('th.post.link', 'th_pay_id', 'Post link')
    state = fields.Selection(selection=[('draft', 'Chờ duyệt'), ('accept', 'Duyệt'), ('paid', 'Đã Thanh toán')])
    th_count_link = fields.Integer('Số bài đăng', default=0, compute="_compute_amount")
    th_payed = fields.Char('Tổng')

    @api.depends('th_post_link_ids')
    def _compute_amount(self):
        for rec in self:
            post_link = rec.th_post_link_ids
            total_pay = 0
            if rec.th_post_link_ids:
                rec.th_count_link = len(post_link.ids)
                for record in post_link:
                    total_pay += float(record.th_expense)
                rec.th_payed = total_pay
            else:
                rec.th_count_link = 0
                rec.th_payed = 0


