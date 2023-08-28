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
    state = fields.Selection(selection=[('pending', 'Chờ duyệt'), ('accept', 'Duyệt'), ('cancel', 'Hủy'), ('paid', 'Đã Thanh toán')], tracking=True)
    th_count_correct_link = fields.Integer('Số bài đăng đúng', default=0, compute="_compute_count_post_link")
    th_count_wrong_link = fields.Integer('Số bài đăng không đạt', default=0, compute="_compute_count_post_link")
    th_paid = fields.Float('Tổng chi phí', default=0)
    th_paid_date = fields.Date('Ngày chi trả')
    th_currency_id = fields.Many2one(comodel_name='res.currency', string='Đơn vị tiền tệ', default=lambda self: self.env.company.currency_id)

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if res['models'].get('th.post.link'):
            res['models']['th.post.link']['state']['selection'] = res['models']['th.post.link']['state']['selection'][1:4]
        return res

    @api.depends('th_post_link_ids')
    def _compute_count_post_link(self):
        for rec in self:
            rec.th_count_wrong_link = len(rec.th_post_link_ids.filtered(lambda l: l.state == 'wrong_request'))
            rec.th_count_correct_link = len(rec.th_post_link_ids.filtered(lambda l: l.state != 'wrong_request'))
            rec.th_paid = sum(rec.th_post_link_ids.filtered(lambda l: l.state not in ['wrong_request']).mapped('th_expense'))

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
