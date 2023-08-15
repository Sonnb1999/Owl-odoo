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
                raise ValidationError('chỉ xóa ở trang thái chờ nghiêm thu')
        res = super().unlink()



