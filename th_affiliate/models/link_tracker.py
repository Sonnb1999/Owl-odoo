from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024


class LinkTracker(models.Model):
    _name = 'link.tracker'
    _inherit = ['link.tracker', 'mail.thread', 'mail.activity.mixin']

    th_link_seeding_id = fields.Many2one('th.link.seeding', string="Link gốc")
    th_type = fields.Selection(selection=[('email_marketing', 'Email marketing'), ('link_seeding', 'Link seeding')])
    th_post_link_ids = fields.One2many('th.post.link', 'link_tracker_id', 'Post link')
    th_partner_id = fields.Many2one('res.partner', 'Cộng tác viên', readonly=True)
    th_total_cost = fields.Float('Tổng chi phí', compute="_amount_all", store=True)
    th_closing_work = fields.Selection(selection=[('no', 'Nghiệm thu'), ('yes', 'Chốt chi phí')], string='Chốt chi phí', tracking=True, default='draft')
    th_image = fields.Binary(related='th_link_seeding_id.th_image')
    th_product_aff_id = fields.Many2one(related='th_link_seeding_id.th_product_aff_id', store=True)
    th_aff_category_id = fields.Many2one(related='th_product_aff_id.th_aff_category_id', store=True)

    @api.depends('th_post_link_ids.th_pay')
    def _amount_all(self):
        total = 0
        link_posts = self.th_post_link_ids
        for link_post in link_posts:
            if link_post.th_pay and link_post.state == "correct_request":
                total = total + float(link_post.th_pay)
        self.th_total_cost = total

    def action_closing_work(self):
        for rec in self:
            rec.write({
                'th_closing_work': 'yes'
            })

    def action_cancel_closing_work(self):
        for rec in self:
            rec.write({
                'th_closing_work': 'no'
            })
