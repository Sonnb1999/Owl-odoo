import uuid

from odoo import tools, models, fields, api, _
from collections import defaultdict
from odoo.exceptions import ValidationError

URL_MAX_SIZE = 10 * 1024 * 1024

select_closing_work = ([
        ('pending', 'Chờ nghiệm thu'),
        ('acceptance', 'Nghiệm thu'),
        ('cost_closing', 'Chốt chi phí')])


class LinkTracker(models.Model):
    _name = 'link.tracker'
    _inherit = ['link.tracker', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'th_product_aff_id'

    th_link_seeding_id = fields.Many2one('th.link.seeding', string="Link gốc")
    th_type = fields.Selection(selection=[('email_marketing', 'Email marketing'), ('link_seeding', 'Link seeding')])
    th_post_link_ids = fields.One2many('th.post.link', 'link_tracker_id', 'Post link')
    th_aff_partner_id = fields.Many2one('res.partner', 'Cộng tác viên', readonly=True)
    th_total_cost = fields.Float('Tổng chi phí', compute="_amount_all", store=True)
    th_closing_work = fields.Selection(selection=select_closing_work, string='Chốt chi phí', tracking=True, default='pending')
    th_image = fields.Binary(related='th_link_seeding_id.th_image')
    th_product_aff_id = fields.Many2one(related='th_link_seeding_id.th_product_aff_id', store=True)
    th_aff_category_id = fields.Many2one(related='th_product_aff_id.th_aff_category_id', store=True)
    th_count_link_click = fields.Integer('Số người dùng nhấn vào link', default=1)
    th_session_user_ids = fields.One2many('th.session.user', 'th_link_tracker_id')
    th_count_user = fields.Integer('Số người dùng', compute="_compute_th_session_user_ids", store=True)

    def th_action_view_statistics(self):
        action = self.env['ir.actions.act_window']._for_xml_id('th_affiliate.th_session_user_action')
        action['domain'] = [('th_link_tracker_id', '=', self.id)]
        action['context'] = dict(self._context, create=False)
        return action
    @api.depends('th_session_user_ids.th_link_tracker_id')
    def _compute_th_session_user_ids(self):
        if self.ids:
            clicks_data = self.env['th.session.user']._read_group(
                [('th_link_tracker_id', 'in', self.ids)],
                ['th_link_tracker_id'],
                ['th_link_tracker_id']
            )
            for m in clicks_data:
                m
            mapped_data = {m['th_link_tracker_id'][0]: m['th_link_tracker_id_count'] for m in clicks_data}
        else:
            mapped_data = dict()
        for tracker in self:
            tracker.th_count_user = mapped_data.get(tracker.id, 0)

    def action_view_count_link_click(self):
        pass

    @api.depends('th_post_link_ids.th_expense')
    def _amount_all(self):
        total = 0
        link_posts = self.th_post_link_ids
        for link_post in link_posts:
            if link_post.th_expense and link_post.state == "correct_request":
                total = total + float(link_post.th_expense)
        self.th_total_cost = total

    def action_closing_work(self):
        for rec in self:
            if rec.th_post_link_ids.filtered(lambda p: p.state == 'pending'):
                raise ValidationError(_("Vui lòng duyệt toàn bộ các bài đăng của cộng tác viên!"))
            if rec.th_post_link_ids.filtered(lambda p: p.state == 'correct_request' and not p.th_seeding_acceptance_id):
                raise ValidationError(_("Vui lòng nhập đủ 'hệ số' cho các bài đăng 'đúng yêu cầu'!"))

            pay_id = self.env['th.pay'].search([('th_partner_id', '=', rec.th_aff_partner_id.id), ('state', '=', 'pending')], limit=1, order='id desc')
            post_link_ids = rec.th_post_link_ids.filtered(lambda p: p.state == 'correct_request' and p.th_seeding_acceptance_id)
            if not pay_id:
                pay_id = self.env['th.pay'].create({
                    'name': _('Phiếu thanh toán cho %s ngày %s', rec.th_aff_partner_id.name, fields.Date.today()),
                    'th_partner_id': rec.th_aff_partner_id.id,
                    'state': 'pending'
                })
            post_link_ids.write({'th_pay_id': pay_id.id})
            rec.write({'th_closing_work': 'cost_closing'})

    def action_cancel_closing_work(self):
        for rec in self:
            rec.write({'th_closing_work': 'acceptance'})

    def unlink(self):
        for rec in self:
            if rec.th_closing_work != 'pending':
                raise ValidationError('Chỉ xóa link ở trang thái chờ nghiêm thu')
        return super().unlink()
