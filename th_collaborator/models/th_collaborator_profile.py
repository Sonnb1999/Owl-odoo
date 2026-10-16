# -*- coding: utf-8 -*-
import logging
import re
import secrets

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tools import email_normalize
from odoo.tools.mimetypes import guess_mimetype

_logger = logging.getLogger(__name__)

TH_CONTRACT_ALLOWED_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png')


class ThCollaboratorProfile(models.Model):
    _name = 'th.collaborator.profile'
    _description = 'Cộng tác viên'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    def th_default_user_id(self):
        """Mặc định người phụ trách CTV là người tạo bản ghi."""
        return self.env.user

    def th_default_access_token(self):
        """Sinh token ngẫu nhiên cho link upload công khai của CTV."""
        return secrets.token_urlsafe(32)

    name = fields.Char(string='Họ và tên', tracking=True)
    th_email = fields.Char(string='Email', tracking=True)
    th_phone = fields.Char(string='Số điện thoại', tracking=True)
    th_phone_normalized = fields.Char(
        string='SĐT chuẩn hoá', compute='th_compute_phone_normalized', store=True, index=True)
    user_id = fields.Many2one(
        'res.users', string='Người phụ trách', tracking=True,
        default=lambda self: self.th_default_user_id())
    state = fields.Selection([
        ('draft', 'Mới'),
        ('sent', 'Đã gửi mail'),
        ('uploaded', 'CTV đã tải hợp đồng'),
    ], string='Trạng thái', default='draft', tracking=True)
    th_company_attachment_ids = fields.Many2many(
        'ir.attachment', 'th_collaborator_profile_company_attachment_rel',
        'th_profile_id', 'th_attachment_id', string='Hợp đồng công ty')
    th_self_attachment_ids = fields.Many2many(
        'ir.attachment', 'th_collaborator_profile_self_attachment_rel',
        'th_profile_id', 'th_attachment_id', string='Hợp đồng CTV tải lên')
    th_access_token = fields.Char(
        string='Token upload', copy=False, default=lambda self: self.th_default_access_token())
    th_upload_url = fields.Char(string='Link upload hợp đồng', compute='th_compute_upload_url')
    th_mail_sent_date = fields.Datetime(string='Ngày gửi mail', copy=False)
    th_last_upload_date = fields.Datetime(string='Ngày CTV tải lên', copy=False)

    _sql_constraints = [
        ('th_phone_normalized_uniq', 'unique(th_phone_normalized)',
         'Số điện thoại đã tồn tại ở một CTV khác.'),
        ('th_access_token_uniq', 'unique(th_access_token)', 'Token upload bị trùng.'),
    ]

    @api.model
    def _normalize_phone(self, phone):
        """Chuẩn hoá SĐT về dạng 0xxxxxxxxx để làm khoá map bản ghi."""
        digits = re.sub(r'\D', '', phone or '')
        if digits.startswith('84') and len(digits) >= 11:
            digits = '0' + digits[2:]
        return digits

    @api.model
    def _is_allowed_contract_file(self, file_name, content=None, mimetype=None):
        """Kiểm tra file hợp đồng upload thường chỉ là PDF hoặc ảnh.

        Kiểm tra cả đuôi file lẫn nội dung thật để chặn file đổi đuôi.
        """
        if not (file_name or '').lower().endswith(TH_CONTRACT_ALLOWED_EXTENSIONS):
            return False
        if content is not None:
            mimetype = guess_mimetype(content)
        return bool(mimetype) and (mimetype == 'application/pdf' or mimetype.startswith('image/'))

    @api.depends('th_phone')
    def th_compute_phone_normalized(self):
        """Tính SĐT chuẩn hoá từ SĐT người dùng nhập."""
        for rec in self:
            rec.th_phone_normalized = self._normalize_phone(rec.th_phone) or False

    @api.depends('th_access_token')
    def th_compute_upload_url(self):
        """Dựng link công khai để CTV tự tải hợp đồng lên."""
        for rec in self:
            rec.th_upload_url = rec.th_access_token and '%s/th_collaborator/upload/%s' % (
                rec.get_base_url(), rec.th_access_token) or False

    @api.constrains('th_email')
    def th_check_email(self):
        """Kiểm tra email CTV đúng định dạng để gửi mail được."""
        for rec in self:
            if rec.th_email and not email_normalize(rec.th_email):
                raise ValidationError(_('Email "%s" không hợp lệ.') % rec.th_email)

    @api.constrains('th_phone')
    def th_check_phone(self):
        """Kiểm tra SĐT đủ độ dài vì SĐT là khoá để CTV xác thực khi upload."""
        for rec in self:
            if rec.th_phone and len(rec.th_phone_normalized or '') < 9:
                raise ValidationError(_('Số điện thoại "%s" không hợp lệ.') % rec.th_phone)

    @api.model_create_multi
    def create(self, vals_list):
        """Tạo CTV và gắn file hợp đồng vào đúng bản ghi."""
        records = super().create(vals_list)
        records._link_contract_attachments()
        return records

    def write(self, vals):
        """Cập nhật CTV và gắn lại file hợp đồng mới thêm vào đúng bản ghi."""
        res = super().write(vals)
        if 'th_company_attachment_ids' in vals or 'th_self_attachment_ids' in vals:
            self._link_contract_attachments()
        return res

    def _link_contract_attachments(self):
        """Gắn res_model/res_id cho file hợp đồng.

        File upload khi bản ghi chưa lưu có res_id = 0; cần gắn lại để quyền xem file
        đi theo quyền của bản ghi CTV và file bị xoá cùng bản ghi.
        """
        for rec in self:
            attachments = (rec.th_company_attachment_ids | rec.th_self_attachment_ids).filtered(
                lambda att: att.res_model != rec._name or att.res_id != rec.id)
            if attachments:
                attachments.write({'res_model': rec._name, 'res_id': rec.id})

    def _add_self_contracts(self, files):
        """Lưu hợp đồng do CTV tự tải lên qua link công khai.

        :param files: list tuple (tên file, nội dung bytes)
        """
        self.ensure_one()
        attachments = self.env['ir.attachment'].create([{
            'name': file_name,
            'raw': content,
            'res_model': self._name,
            'res_id': self.id,
        } for file_name, content in files])
        self.write({
            'th_self_attachment_ids': [Command.link(att.id) for att in attachments],
            'state': 'uploaded',
            'th_last_upload_date': fields.Datetime.now(),
        })
        self.message_post(
            body=_('CTV đã tải lên %s file hợp đồng: %s') % (
                len(attachments), ', '.join(attachments.mapped('name'))),
            subtype_xmlid='mail.mt_comment')
        _logger.info('Collaborator %s uploaded %s contract file(s)', self.id, len(attachments))
        return attachments

    def _send_contract_mail(self):
        """Gửi mail mời CTV tải hợp đồng từ email người phụ trách, kèm hợp đồng công ty (nếu có)."""
        missing = self.filtered(lambda rec: not rec.th_email)
        if missing:
            raise UserError(_('Các CTV sau chưa có email:\n%s') % '\n'.join(missing.mapped('name')))
        missing_sender = self.filtered(lambda rec: not rec.user_id.email)
        if missing_sender:
            raise UserError(_('Các CTV sau chưa có người phụ trách hoặc người phụ trách chưa có email:\n%s')
                            % '\n'.join(missing_sender.mapped('name')))
        template = self.env.ref('th_collaborator.th_collaborator_profile_upload_mail_template')
        for rec in self:
            # Ép email_from theo người phụ trách ngay cả khi template (noupdate) chưa được cập nhật
            # force_send=False: đưa vào hàng đợi mail cron, tránh treo request khi gửi số lượng lớn
            template.send_mail(rec.id, force_send=True, email_values={
                'email_from': rec.user_id.email_formatted,
                'reply_to': rec.user_id.email_formatted,
                'attachment_ids': rec.th_company_attachment_ids.ids,
            })
        self.filtered(lambda rec: rec.state == 'draft').write({'state': 'sent'})
        self.write({'th_mail_sent_date': fields.Datetime.now()})
        _logger.info('Queued contract mail for %s collaborator(s)', len(self))

    def th_action_send_contract_mail(self):
        """Nút gửi mail hợp đồng cho 1 CTV trên form."""
        self.ensure_one()
        self._send_contract_mail()
        return True

    def th_action_send_contract_mail_batch(self):
        """Gửi mail hợp đồng cho nhiều CTV được chọn trên list view."""
        self._send_contract_mail()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Đã đưa %s mail vào hàng đợi gửi.') % len(self),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def th_action_regenerate_token(self):
        """Tạo lại link upload, vô hiệu hoá link cũ đã gửi cho CTV."""
        self.ensure_one()
        self.th_access_token = self.th_default_access_token()
        self.message_post(body=_('Đã tạo lại link upload hợp đồng, link cũ không còn hiệu lực.'))
        return True

    def th_action_download_contracts(self):
        """Tải toàn bộ hợp đồng của các CTV được chọn dưới dạng 1 file ZIP."""
        if not self:
            raise UserError(_('Vui lòng chọn ít nhất 1 CTV.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/th_collaborator/download_zip?ids=%s' % ','.join(str(rec_id) for rec_id in self.ids),
            'target': 'new',
        }
