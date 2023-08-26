from odoo import tools, models, fields, api, _
from collections import defaultdict
from odoo.exceptions import ValidationError
URL_MAX_SIZE = 10 * 1024 * 1024

select_state = [
    ('pending', 'Chờ duyệt'),
    ('correct_request', 'Đúng yêu cầu'),
    ('wrong_request', 'Sai yêu cầu'),
    ('paid', 'Đã thanh toán')
]


class ThPostSeeding(models.Model):
    _name = "th.post.link"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char('Link bài đăng', tracking=True, required=True)
    link_tracker_id = fields.Many2one('link.tracker')
    th_note = fields.Text('Comment', tracking=True)
    th_acceptance_person_id = fields.Many2one('res.partner', string='Nghiệm thu', readonly=1, tracking=True)
    th_seeding_acceptance_ids = fields.Many2many(comodel_name='th.acceptance.seeding', string='Hệ số', tracking=True)
    th_expense = fields.Char('Chi phí', compute="compute_th_expense")
    state = fields.Selection(selection=select_state, string='Trạng thái', tracking=True, default='pending', required=True)
    th_campaign_id = fields.Many2one(related="link_tracker_id.campaign_id", store=True)
    th_pay_id = fields.Many2one(comodel_name="th.pay", string="Pay")
    # th_link_owner_id = fields.Many2one('res.partner', 'Người sở hữu')
    # th_nick = fields.Char('Tên nick')
    th_check_uid = fields.Boolean('Kiểm tra', compute="compute_th_expense")

    @api.depends('th_seeding_acceptance_ids')
    def compute_th_expense(self):
        for rec in self:
            if rec.link_tracker_id and rec.link_tracker_id.create_uid.id == self._uid:
                rec.th_check_uid = True
            else:
                rec.th_check_uid = False

            acceptance_seeding = rec.th_seeding_acceptance_ids
            create_date = rec.create_date.date() if rec.create_date else fields.Date.today()
            th_cost = 0
            
            for rec2 in acceptance_seeding:
                if rec2:
                    cost_histories = rec2.th_acceptance_cost_history_ids
                    if cost_histories:
                        for cost_history in cost_histories:
                            #  ngày tạo chi phí trong quá khứ <= nếu ngày tạo bài đăng <= ngày kết thúc trong quá khứ
                            if cost_history.th_end_date and cost_history.th_start_date <= create_date <= cost_history.th_end_date:
                                th_cost += cost_history.th_factor
                            elif cost_history.th_start_date <= create_date and not cost_history.th_end_date:
                                th_cost += cost_history.th_cost_factor
                            else:
                                th_cost
            rec.th_expense = th_cost



    def action_visit_page(self):
        return {
            'name': _("Đến trang"),
            'type': 'ir.actions.act_url',
            'url': self.name,
            'target': 'new',
        }

    def write(self, values):
        state = values.get('state', False)
        th_seeding_acceptance_ids = values.get('th_seeding_acceptance_ids', False)
        for rec in self:
            if (state or th_seeding_acceptance_ids) and rec.th_acceptance_person_id.id != self.env.user.partner_id.id:
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
            if rec.link_tracker_id and rec.link_tracker_id.th_closing_work == 'cost_closing':
                raise ValidationError('Đang trong quá trình chốt chi phí không thể tạo thêm link!')
        return rec
