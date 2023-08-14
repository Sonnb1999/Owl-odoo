from odoo import tools, models, fields, api, _
from collections import defaultdict

URL_MAX_SIZE = 10 * 1024 * 1024

select_state = [
    ('pending', 'Chờ duyệt'),
    ('correct_request', 'Đúng yêu cầu'),
    ('wrong_request', 'Sai yêu cầu')
]


class ThPostSeeding(models.Model):
    _name = "th.post.link"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Post link', tracking=True, required=True)
    link_tracker_id = fields.Many2one('link.tracker')
    th_note = fields.Text('Comment', tracking=True)
    th_acceptance_person_id = fields.Many2one('res.partner', string='Nghiệm thu', readonly=1, tracking=True)
    th_seeding_acceptance_id = fields.Many2one('th.acceptance.seeding', 'Hệ số', tracking=True)
    th_expense = fields.Char('Chi phí', compute="compute_th_expense")
    state = fields.Selection(selection=select_state, string='Trạng thái', tracking=True)
    th_campaign_id = fields.Many2one(related="link_tracker_id.campaign_id", store=True)
    th_pay_id = fields.Many2one(comodel_name="th.pay", string="Pay")
    # th_link_owner_id = fields.Many2one('res.partner', 'Người sở hữu')

    @api.depends('th_seeding_acceptance_id')
    def compute_th_expense(self):
        for rec in self:
            new_pay = rec.th_seeding_acceptance_id
            old_pays = new_pay.th_acceptance_cost_history_ids
            if new_pay and old_pays:
                for old_pay in old_pays:
                    if old_pay.th_end_date and old_pay.th_start_date <= rec.create_date.date() <= old_pay.th_end_date:
                        rec.th_expense = old_pay.th_cost_factor
                    elif old_pay.th_start_date <= rec.create_date.date() and not old_pay.th_end_date:
                        rec.th_expense = old_pay.th_cost_factor
                    else:
                        rec.th_expense
            else:
                rec.th_expense = False

    def action_visit_page(self):
        return {
            'name': _("Đến trang"),
            'type': 'ir.actions.act_url',
            'url': self.name,
            'target': 'new',
        }

    def write(self, values):
        state = values.get('state', False)
        th_seeding_acceptance_id = values.get('th_seeding_acceptance_id', False)
        for rec in self:
            if (state or th_seeding_acceptance_id) and rec.th_acceptance_person_id.id != self.env.user.partner_id.id:
                values['th_acceptance_person_id'] = self.env.user.partner_id.id

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
