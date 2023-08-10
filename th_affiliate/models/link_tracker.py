from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024

select_state = [
    ('pending', 'Chờ duyệt'),
    ('correct_request', 'Đúng yêu cầu'),
    ('wrong_request', 'Sai yêu cầu')
]


class LinkTracker(models.Model):
    _name = 'link.tracker'
    _inherit = ['link.tracker', 'mail.thread', 'mail.activity.mixin']

    th_link_seeding_id = fields.Many2one('th.link.seeding', string="Link gốc")
    th_type = fields.Selection(selection=[('email_marketing', 'Email marketing'), ('link_seeding', 'Link seeding')])
    th_category = fields.Selection(selection=[('in_category', 'Trong danh mục'), ('out_of_category', 'Ngoài danh mục')])
    th_post_link_ids = fields.One2many('th.post.link', 'link_tracker_id', 'Post link')
    th_partner_id = fields.Many2one('res.partner', 'Đối tác', readonly=True)
    th_image = fields.Binary(string="Ảnh sản phẩm")
    th_total_cost = fields.Float('Tổng chi phí', compute="_amount_all", store=True)
    th_closing_work = fields.Boolean('Chốt chi phí', default=False, tracking=True)

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
            if not rec.th_closing_work:
                rec.write({
                    'th_closing_work': True
                })


class ThPostSeeding(models.Model):
    _name = "th.post.link"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char('Post link', tracking=True, required=True)
    link_tracker_id = fields.Many2one('link.tracker')
    th_note = fields.Text('Comment', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Nghiệm thu', readonly=1, tracking=True)
    th_seeding_acceptance_id = fields.Many2one('th.acceptance.seeding', 'Hệ số', tracking=True)
    th_pay = fields.Char('Chi phí', compute="compute_th_pay")
    state = fields.Selection(selection=select_state, string='Trạng thái', tracking=True)

    @api.depends('th_seeding_acceptance_id')
    def compute_th_pay(self):
        for rec in self:
            new_pay = rec.th_seeding_acceptance_id
            old_pays = new_pay.th_acceptance_cost_history_ids
            if new_pay and old_pays:
                for old_pay in old_pays:
                    if old_pay.th_end_date and old_pay.th_start_date <= rec.create_date.date() <= old_pay.th_end_date:
                        rec.th_pay = old_pay.th_cost_factor
                    elif old_pay.th_start_date <= rec.create_date.date() and not old_pay.th_end_date:
                        rec.th_pay = old_pay.th_cost_factor
                    else:
                        rec.th_pay
            else:
                rec.th_pay = False

    def write(self, values):
        state = values.get('state', False)
        th_seeding_acceptance_id = values.get('th_seeding_acceptance_id', False)
        for rec in self:
            if (state or th_seeding_acceptance_id) and rec.partner_id.id != self.env.user.partner_id.id:
                values['partner_id'] = self.env.user.partner_id.id

        link_post_initial_values = defaultdict(dict)
        tracking_fields = []
        for field_name in values:
            field = self._fields[field_name]
            if not (hasattr(field, 'related') and field.related) and hasattr(field, 'tracking') and field.tracking:
                tracking_fields.append(field_name)
        fields_definition = self.env['th.post.link'].fields_get(tracking_fields)

        for link_post in self:
            for field in tracking_fields:
                link_post_initial_values[link_post][field] = link_post[field]

        res = super().write(values)
        for link_post, initial_values in link_post_initial_values.items():
            tracking_value_ids = link_post._mail_track(fields_definition, initial_values)[1]
            if tracking_value_ids:
                msg = _("Link bài đăng %s đã được cập nhập", link_post._get_html_link(title=f"#{link_post.id}"))
                link_post.link_tracker_id._message_log(body=msg, tracking_value_ids=tracking_value_ids)
        return res

    @api.model
    def create(self, values):
        result = super(ThPostSeeding, self).create(values)
        for rec in result:
            if rec.link_tracker_id and rec.link_tracker_id.th_closing_work:
                return False
        return rec