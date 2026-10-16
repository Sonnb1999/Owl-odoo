# -*- coding: utf-8 -*-
import base64
import io
import logging
import os
import re
import secrets

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tools import email_normalize
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.pdf import PdfFileReader

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
    th_contract_name = fields.Char(string='Tên hợp đồng', tracking=True)
    th_contract_type_ids = fields.Many2many(
        'th.collaborator.contract.type', 'th_collaborator_profile_contract_type_rel',
        'th_profile_id', 'th_contract_type_id', string='Loại hợp đồng')
    th_contract_template_id = fields.Many2one(
        'th.collaborator.contract.template', string='Template hợp đồng', tracking=True)
    th_filled_attachment_id = fields.Many2one(
        'ir.attachment', string='Hợp đồng đã đục lỗ', copy=False)
    th_sign_config_id = fields.Many2one(related='th_contract_template_id.th_sign_config_id')
    th_is_signed = fields.Boolean(string='Bên A đã ký số', copy=False, tracking=True)
    th_signed_date = fields.Datetime(string='Thời gian ký số', copy=False)
    th_signer_id = fields.Many2one('res.users', string='Người ký số', copy=False)
    th_signer_cert_info = fields.Char(string='Chứng thư số', copy=False)

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

    def _build_self_contract_file_names(self, original_names):
        """Đặt tên hợp đồng CTV theo dạng SĐT_Tên.<đuôi gốc> để dễ tra cứu.

        File đầu tiên của CTV là SĐT_Tên.pdf, các file sau đánh số tiếp SĐT_Tên_2.pdf...
        dựa trên số file đã có để không trùng tên giữa các lần upload.
        """
        self.ensure_one()
        base_name = re.sub(r'[\\/:*?"<>|]+', '_', '%s_%s' % (self.th_phone_normalized or '', self.name or '')).strip()
        index = len(self.th_self_attachment_ids)
        file_names = []
        for original_name in original_names:
            index += 1
            extension = os.path.splitext(original_name or '')[1].lower()
            suffix = '_%s' % index if index > 1 else ''
            file_names.append('%s%s%s' % (base_name, suffix, extension))
        return file_names

    def _add_self_contracts(self, files):
        """Lưu hợp đồng do CTV tự tải lên qua link công khai.

        :param files: list tuple (tên file, nội dung bytes)
        """
        self.ensure_one()
        file_names = self._build_self_contract_file_names([file_name for file_name, dummy in files])
        attachments = self.env['ir.attachment'].create([{
            'name': file_name,
            'raw': content,
            'res_model': self._name,
            'res_id': self.id,
        } for file_name, (dummy, content) in zip(file_names, files)])
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

    def _get_contract_field_values(self):
        """Giá trị điền vào các ô form theo cấu hình đục lỗ của template đã chọn."""
        self.ensure_one()
        return self.th_contract_template_id._get_field_values(self)

    def _replace_company_contract(self, new_attachment):
        """Thay hợp đồng do hệ thống tạo trong Hợp đồng công ty bằng file mới, giữ các file khác."""
        self.ensure_one()
        old_attachment = self.th_filled_attachment_id
        commands = [Command.link(new_attachment.id)]
        if old_attachment:
            commands.insert(0, Command.unlink(old_attachment.id))
        self.write({'th_company_attachment_ids': commands, 'th_filled_attachment_id': new_attachment.id})
        # Bản cũ chưa từng gửi mail thì xoá hẳn; đã gửi thì giữ vì mail trong chatter còn tham chiếu
        if old_attachment and not self.env['mail.message'].search_count(
                [('attachment_ids', 'in', old_attachment.ids)]):
            old_attachment.unlink()

    def _create_company_contract(self):
        """Đục lỗ template với thông tin CTV và lưu vào Hợp đồng công ty, thay bản đã tạo trước đó.

        Bản mới chưa có chữ ký số nên trạng thái ký được đặt lại.
        """
        Attachment = self.env['ir.attachment']
        missing_template = self.filtered(lambda rec: not rec.th_contract_template_id)
        if missing_template:
            raise UserError(_('Các CTV sau chưa chọn template hợp đồng:\n%s')
                            % '\n'.join(missing_template.mapped('name')))
        for rec in self:
            pdf_data = rec.th_contract_template_id._render_filled_pdf(rec._get_contract_field_values())
            file_name = re.sub(r'[\\/:*?"<>|]+', '_', '%s_%s_%s.pdf' % (
                rec.th_phone_normalized or '', rec.name or '', rec.th_contract_template_id.name or ''))
            rec._replace_company_contract(Attachment.create({
                'name': file_name,
                'raw': pdf_data,
                'mimetype': 'application/pdf',
                'res_model': rec._name,
                'res_id': rec.id,
            }))
            rec.write({'th_is_signed': False, 'th_signed_date': False, 'th_signer_id': False,
                       'th_signer_cert_info': False})
            rec.message_post(body=_('Đã tạo hợp đồng "%s" từ template "%s".') % (
                file_name, rec.th_contract_template_id.name))

    def _send_contract_mail(self):
        """Gửi mail hợp đồng từ email người phụ trách, kèm các file Hợp đồng công ty."""
        missing = self.filtered(lambda rec: not rec.th_email)
        if missing:
            raise UserError(_('Các CTV sau chưa có email:\n%s') % '\n'.join(missing.mapped('name')))
        # Mail mời CTV ký hợp đồng nên bắt buộc phải có hợp đồng công ty hoặc template để đục lỗ
        missing_contract = self.filtered(
            lambda rec: not rec.th_company_attachment_ids and not rec.th_contract_template_id)
        if missing_contract:
            raise UserError(_('Các CTV sau chưa có hợp đồng công ty hoặc template hợp đồng:\n%s')
                            % '\n'.join(missing_contract.mapped('name')))
        missing_sender = self.filtered(lambda rec: not rec.user_id.email)
        if missing_sender:
            raise UserError(_('Các CTV sau chưa có người phụ trách hoặc người phụ trách chưa có email:\n%s')
                            % '\n'.join(missing_sender.mapped('name')))
        # Template yêu cầu bên A ký số thì phải ký xong mới được gửi cho CTV
        missing_sign = self.filtered(lambda rec: rec.th_sign_config_id and not rec.th_is_signed)
        if missing_sign:
            raise UserError(_('Hợp đồng của các CTV sau chưa được bên A ký số:\n%s')
                            % '\n'.join(missing_sign.mapped('name')))
        # CTV chưa có hợp đồng công ty nhưng đã chọn template thì tự tạo trước khi gửi;
        # đã có thì gửi đúng bản người dùng đã tạo/kiểm tra, không đục lỗ lại
        self.filtered(lambda rec: not rec.th_company_attachment_ids)._create_company_contract()
        default_template = self.env.ref('th_collaborator.th_collaborator_profile_upload_mail_template')
        for rec in self:
            mail_template = rec.th_contract_template_id.th_mail_template_id or default_template
            # Ép email_from theo người phụ trách ngay cả khi mẫu mail cấu hình địa chỉ khác
            # force_send=False: đưa vào hàng đợi mail cron, tránh treo request khi gửi số lượng lớn
            mail_template.send_mail(rec.id, force_send=True, email_values={
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

    def th_action_create_contract(self):
        """Nút tạo hợp đồng từ template và lưu vào Hợp đồng công ty."""
        self.ensure_one()
        self._create_company_contract()
        return True

    # ------------------------------------------------------------------
    # Ký số bên A (không phụ thuộc nhà cung cấp, xem th.collaborator.sign.config)
    # ------------------------------------------------------------------

    def _check_can_sign(self):
        """Kiểm tra các hợp đồng đã sẵn sàng để bên A ký số."""
        errors = []
        for rec in self:
            config = rec.th_sign_config_id
            if not config:
                errors.append(_('%s: template hợp đồng chưa cấu hình ký số.') % rec.name)
            elif not config._get_provider_sign_mode():
                errors.append(_('%s: chưa chọn nhà cung cấp chữ ký số hoặc chưa cài module nhà cung cấp.') % rec.name)
            elif not rec.th_filled_attachment_id:
                errors.append(_('%s: chưa tạo hợp đồng từ template.') % rec.name)
            elif rec.th_is_signed:
                errors.append(_('%s: hợp đồng đã được ký.') % rec.name)
        if errors:
            raise UserError(_('Không thể ký số:\n%s') % '\n'.join(errors))
        for template in self.mapped('th_contract_template_id'):
            template._get_sign_box()

    @api.model
    def _get_pdf_page_count(self, pdf_data):
        """Số trang PDF, dùng cho tuỳ chọn ký nháy tất cả các trang."""
        return PdfFileReader(io.BytesIO(pdf_data), strict=False).getNumPages()

    def _get_sign_action(self):
        """Ký các hợp đồng: nhà cung cấp kiểu server ký ngay, kiểu client chuyển xuống trình duyệt."""
        self._check_can_sign()
        server_records = self.filtered(lambda rec: rec.th_sign_config_id._get_provider_sign_mode() == 'server')
        for rec in server_records:
            pdf_data = rec.th_filled_attachment_id.raw
            result = rec.th_sign_config_id._sign_pdf_server(
                pdf_data, rec.th_contract_template_id._get_sign_box(), self._get_pdf_page_count(pdf_data))
            rec._save_signed_contract(result['signed_pdf'], result.get('cert_base64'))
        client_records = self - server_records
        if client_records:
            return {
                'type': 'ir.actions.client',
                'tag': 'th_collaborator.sign_contracts',
                'params': {'profile_ids': client_records.ids},
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Đã ký số %s hợp đồng.') % len(server_records),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def th_action_sign_contract(self):
        """Nút ký số hợp đồng bên A trên form CTV."""
        self.ensure_one()
        return self._get_sign_action()

    def th_action_sign_contract_batch(self):
        """Ký số hàng loạt hợp đồng các CTV được chọn trên list view."""
        return self._get_sign_action()

    def th_get_sign_payloads(self):
        """Dữ liệu để trình duyệt ký số (nhà cung cấp kiểu client): file PDF, vị trí ô ký, tuỳ chọn hiển thị."""
        self._check_can_sign()
        configs = {}
        items = []
        for rec in self:
            config = rec.th_sign_config_id
            # Khoá dạng chuỗi để serialize được qua cả JSON-RPC lẫn XML-RPC
            config_key = str(config.id)
            if config_key not in configs:
                configs[config_key] = {
                    'provider': config.th_provider,
                    'options': config._get_client_sign_options(),
                }
            pdf_data = rec.th_filled_attachment_id.raw
            items.append({
                'profile_id': rec.id,
                'name': rec.name,
                'attachment_id': rec.th_filled_attachment_id.id,
                'pdf_base64': base64.b64encode(pdf_data).decode(),
                'page_count': self._get_pdf_page_count(pdf_data),
                'sign_box': rec.th_contract_template_id._get_sign_box(),
                'config_id': config_key,
            })
        return {'configs': configs, 'items': items}

    @api.model
    def th_save_signed_contracts(self, results):
        """Nhận PDF đã ký từ trình duyệt và lưu thay hợp đồng chưa ký.

        :param results: list dict {profile_id, attachment_id, signed_pdf_base64, cert_base64}
        :return: dict {'signed': số hợp đồng đã lưu, 'skipped': tên CTV bị bỏ qua}
        """
        profiles = self.browse([result.get('profile_id') for result in results]).exists()
        profiles.check_access_rights('write')
        profiles.check_access_rule('write')
        profile_by_id = {profile.id: profile for profile in profiles}
        signed_count = 0
        skipped = []
        for result in results:
            rec = profile_by_id.get(result.get('profile_id'))
            if not rec:
                continue
            # Hợp đồng bị tạo lại trong lúc đang ký thì bản vừa ký không còn đúng nội dung
            if rec.th_is_signed or rec.th_filled_attachment_id.id != result.get('attachment_id'):
                skipped.append(rec.name)
                continue
            rec._save_signed_contract(base64.b64decode(result.get('signed_pdf_base64') or ''),
                                      result.get('cert_base64'))
            signed_count += 1
        return {'signed': signed_count, 'skipped': skipped}

    @api.model
    def _get_cert_info(self, cert_base64):
        """Tóm tắt chứng thư số (tên, serial, hạn dùng) để lưu vết người ký."""
        if not cert_base64:
            return False
        try:
            cert = x509.load_der_x509_certificate(base64.b64decode(cert_base64), default_backend())
        except ValueError:
            _logger.warning('Cannot parse signer certificate', exc_info=True)
            return False
        common_names = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
        return '%s | Serial: %x | Hạn: %s' % (
            common_names[0].value if common_names else cert.subject.rfc4514_string(),
            cert.serial_number, cert.not_valid_after.strftime('%d/%m/%Y'))

    def _save_signed_contract(self, signed_pdf, cert_base64=False):
        """Lưu PDF đã ký số vào Hợp đồng công ty và ghi nhận thông tin ký."""
        self.ensure_one()
        if guess_mimetype(signed_pdf) != 'application/pdf' or b'/ByteRange' not in signed_pdf:
            raise UserError(_('File trả về cho CTV %s không phải PDF đã ký số.') % self.name)
        stem = os.path.splitext(self.th_filled_attachment_id.name or self.name or 'hop_dong')[0]
        attachment = self.env['ir.attachment'].create({
            'name': '%s_da_ky.pdf' % stem,
            'raw': signed_pdf,
            'mimetype': 'application/pdf',
            'res_model': self._name,
            'res_id': self.id,
        })
        self._replace_company_contract(attachment)
        cert_info = self._get_cert_info(cert_base64)
        self.write({
            'th_is_signed': True,
            'th_signed_date': fields.Datetime.now(),
            'th_signer_id': self.env.user.id,
            'th_signer_cert_info': cert_info,
        })
        self.message_post(body=_('Bên A đã ký số hợp đồng "%s"%s.') % (
            attachment.name, (' (%s)' % cert_info) if cert_info else ''))
        _logger.info('Collaborator %s: contract signed by user %s', self.id, self.env.uid)

    def th_action_preview_contract(self):
        """Xem trước hợp đồng đục lỗ với thông tin hiện tại của CTV."""
        self.ensure_one()
        if not self.th_contract_template_id:
            raise UserError(_('Vui lòng chọn template hợp đồng trước khi xem trước.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/th_collaborator/contract/preview/profile/%s' % self.id,
            'target': 'new',
        }

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

    def _get_download_contracts_action(self, contract_type):
        """Trả về action tải ZIP 1 loại hợp đồng ('company' | 'self') của các CTV được chọn."""
        if not self:
            raise UserError(_('Vui lòng chọn ít nhất 1 CTV.'))
        field_name = 'th_company_attachment_ids' if contract_type == 'company' else 'th_self_attachment_ids'
        if not self.mapped(field_name):
            raise UserError(_('Các CTV được chọn chưa có file hợp đồng để tải.'))
        return {
            'type': 'ir.actions.act_url',
            'url': '/th_collaborator/download_zip?contract_type=%s&ids=%s' % (
                contract_type, ','.join(str(rec_id) for rec_id in self.ids)),
            'target': 'new',
        }

    def th_action_download_company_contracts(self):
        """Tải hợp đồng công ty của các CTV được chọn dưới dạng 1 file ZIP."""
        return self._get_download_contracts_action('company')

    def th_action_download_self_contracts(self):
        """Tải hợp đồng CTV tự tải lên của các CTV được chọn dưới dạng 1 file ZIP."""
        return self._get_download_contracts_action('self')
