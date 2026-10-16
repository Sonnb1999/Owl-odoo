# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import formatLang, html2plaintext

TH_MAPPABLE_FIELD_TYPES = (
    'char', 'text', 'html', 'selection', 'date', 'datetime',
    'integer', 'float', 'monetary', 'boolean', 'many2one', 'many2many',
)
# Trường kỹ thuật không cho in vào hợp đồng
TH_EXCLUDED_FIELD_NAMES = (
    'id', '__last_update', 'display_name', 'create_uid', 'write_uid', 'write_date',
    'th_access_token', 'th_phone_normalized', 'th_upload_url', 'th_contract_template_id',
)
TH_EXCLUDED_FIELD_PREFIXES = ('message_', 'activity_', 'has_message', 'my_activity_')


class ThCollaboratorContractTemplateLine(models.Model):
    _name = 'th.collaborator.contract.template.line'
    _description = 'Cấu hình đục lỗ template hợp đồng'
    _order = 'sequence, id'

    @api.model
    def _get_mappable_field_selection(self):
        """Danh sách trường CTV được phép đục lỗ vào hợp đồng.

        Dùng selection thay vì Many2one ir.model.fields vì người dùng nội bộ không có quyền đọc ir.model.fields.
        """
        Profile = self.env['th.collaborator.profile']
        selection = []
        for name, field in Profile._fields.items():
            if field.type not in TH_MAPPABLE_FIELD_TYPES or name in TH_EXCLUDED_FIELD_NAMES \
                    or name.startswith(TH_EXCLUDED_FIELD_PREFIXES) or getattr(field, 'comodel_name', None) == 'ir.attachment':
                continue
            selection.append((name, field._description_string(self.env)))
        return sorted(selection, key=lambda item: item[1])

    th_template_id = fields.Many2one(
        'th.collaborator.contract.template', string='Template hợp đồng', ondelete='cascade', index=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    th_pdf_field_name = fields.Char(string='Ô form trong PDF')
    th_field_name = fields.Selection(selection='_get_mappable_field_selection', string='Trường thông tin CTV')
    # Ô vẽ tay trên màn hình thiết kế (PDF không có sẵn ô form); toạ độ theo hệ PDF, đơn vị point
    th_is_manual = fields.Boolean(string='Ô vẽ tay')
    # Ô vị trí chữ ký số bên A: không đục lỗ chữ, chỉ truyền toạ độ cho nhà cung cấp chữ ký
    th_is_signature = fields.Boolean(string='Ô chữ ký bên A')
    th_page = fields.Integer(string='Trang')
    th_pos_x = fields.Float(string='X')
    th_pos_y = fields.Float(string='Y')
    th_width = fields.Float(string='Rộng')
    th_height = fields.Float(string='Cao')
    th_font_size = fields.Float(string='Cỡ chữ')

    _sql_constraints = [
        ('th_pdf_field_name_uniq', 'unique(th_template_id, th_pdf_field_name)',
         'Mỗi ô form chỉ được cấu hình 1 lần trên 1 template.'),
    ]

    def _format_field_value(self, record):
        """Chuyển giá trị trường của CTV thành chuỗi để in vào hợp đồng."""
        self.ensure_one()
        field = record._fields.get(self.th_field_name)
        if not field:
            return ''
        value = record[field.name]
        if field.type == 'boolean':
            return 'Có' if value else 'Không'
        if not value:
            return ''
        if field.type == 'selection':
            return dict(field._description_selection(record.env)).get(value, value)
        if field.type == 'date':
            return value.strftime('%d/%m/%Y')
        if field.type == 'datetime':
            return fields.Datetime.context_timestamp(record, value).strftime('%d/%m/%Y %H:%M')
        if field.type in ('float', 'monetary'):
            return formatLang(record.env, value)
        if field.type in ('many2one', 'many2many'):
            return ', '.join(value.mapped('display_name'))
        if field.type == 'html':
            return html2plaintext(value)
        return str(value)

    def _get_sample_value(self):
        """Giá trị mẫu khi xem thử template: hiện nhãn trường để kiểm tra vị trí đục lỗ."""
        self.ensure_one()
        labels = dict(self._fields['th_field_name']._description_selection(self.env))
        return '<%s>' % labels.get(self.th_field_name, self.th_pdf_field_name)
