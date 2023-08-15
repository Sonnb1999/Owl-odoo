from odoo import tools, models, fields, api, _
from collections import defaultdict
from odoo.exceptions import ValidationError
URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'th.pay'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Phiếu chi trả')
    th_partner_id = fields.Many2one('res.partner', string="Cộng tác viên")
    th_post_link_ids = fields.One2many('th.post.link', 'th_pay_id', 'Post link')
    state = fields.Selection(selection=[('pending', 'Chờ duyệt'), ('accept', 'Duyệt'), ('cancel', 'Hủy'), ('paid', 'Đã Thanh toán')])
    th_count_link = fields.Integer('Số bài đăng', default=0, compute="_compute_amount")
    th_paid = fields.Float('Tổng chi phí')
    th_paid_date = fields.Date('Ngày chi trả')

    @api.depends('th_post_link_ids')
    def _compute_amount(self):
        for rec in self:
            post_link = rec.th_post_link_ids
            total_pay = 0
            if rec.th_post_link_ids:
                rec.th_count_link = len(post_link.ids)
                for record in post_link:
                    total_pay += float(record.th_expense)
                rec.th_paid = total_pay
            else:
                rec.th_count_link = 0
                rec.th_paid = 0

    def action_pending_pay(self):
        for rec in self:
            rec.state = 'pending'

    def action_cancel_pay(self):
        for rec in self:
            rec.state = 'cancel'

    def action_accept_pay(self):
        for rec in self:
            rec.state = 'accept'

    def th_action_paid(self):
        for rec in self:
            rec.state = 'paid'
            rec.th_paid_date = fields.Date.today()

            for record in rec.th_post_link_ids:
                record.state = 'paid'

    def unlink(self):
        for record in self:
            if record.state != 'pending':
                raise ValidationError("Chỉ có thể xóa các bản ghi ở trạng thái chờ duyệt!")
        super(LinkTracker, self).unlink()
