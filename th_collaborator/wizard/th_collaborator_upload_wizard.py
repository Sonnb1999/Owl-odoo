# -*- coding: utf-8 -*-
import base64
import io
import logging
import os
import re
import zipfile

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command

_logger = logging.getLogger(__name__)

TH_ZIP_MAX_FILES = 2000
TH_ZIP_MAX_UNCOMPRESSED_SIZE = 1024 * 1024 * 1024  # 1GB, chặn zip bomb


class ThCollaboratorUploadWizard(models.TransientModel):
    _name = 'th.collaborator.upload.wizard'
    _description = 'Tải hợp đồng CTV hàng loạt'

    th_target_type = fields.Selection([
        ('company', 'Hợp đồng công ty'),
        ('self', 'Hợp đồng CTV'),
    ], string='Loại hợp đồng', default='company')
    th_upload_mode = fields.Selection([
        ('files', 'Nhiều file (PDF/ảnh)'),
        ('zip', 'File ZIP'),
    ], string='Hình thức tải lên', default='files')
    th_attachment_ids = fields.Many2many(
        'ir.attachment', 'th_collaborator_upload_wizard_attachment_rel',
        'th_wizard_id', 'th_attachment_id', string='Các file hợp đồng')
    th_zip_file = fields.Binary(string='File ZIP')
    th_zip_filename = fields.Char(string='Tên file ZIP')
    th_result_note = fields.Text(string='Kết quả')
    th_is_done = fields.Boolean(string='Đã xử lý')

    def _extract_phone(self, file_path):
        """Lấy SĐT từ tên file (SĐT_xxx.pdf), nếu không có thì lấy từ tên thư mục cha."""
        Profile = self.env['th.collaborator.profile']
        parts = [part for part in re.split(r'[\\/]', file_path) if part]
        candidates = [os.path.splitext(parts[-1])[0]] + list(reversed(parts[:-1]))
        for candidate in candidates:
            phone = Profile._normalize_phone(re.split(r'[_\-\s]', candidate)[0])
            if len(phone) >= 9:
                return phone
        return False

    def _extract_zip_files(self):
        """Giải nén file ZIP, trả về list (đường dẫn trong zip, nội dung bytes)."""
        if not self.th_zip_file:
            return []
        try:
            archive = zipfile.ZipFile(io.BytesIO(base64.b64decode(self.th_zip_file)))
        except zipfile.BadZipFile:
            raise UserError(_('File ZIP không hợp lệ.'))
        infos = [
            info for info in archive.infolist()
            if not info.is_dir() and '__MACOSX' not in info.filename
            and not os.path.basename(info.filename).startswith('.')
        ]
        if len(infos) > TH_ZIP_MAX_FILES:
            raise UserError(_('File ZIP chứa quá %s file.') % TH_ZIP_MAX_FILES)
        if sum(info.file_size for info in infos) > TH_ZIP_MAX_UNCOMPRESSED_SIZE:
            raise UserError(_('Dung lượng giải nén của file ZIP vượt quá giới hạn cho phép.'))
        return [(info.filename, archive.read(info)) for info in infos]

    def th_action_import_contracts(self):
        """Map hàng loạt file hợp đồng vào CTV theo SĐT trong tên file/thư mục."""
        self.ensure_one()
        # item: (đường dẫn, attachment đã upload | bytes từ zip)
        if self.th_upload_mode == 'zip':
            items = self._extract_zip_files()
            if not items:
                raise UserError(_('Vui lòng chọn file ZIP.'))
        else:
            if not self.th_attachment_ids:
                raise UserError(_('Vui lòng chọn file hợp đồng.'))
            Profile = self.env['th.collaborator.profile']
            invalid = self.th_attachment_ids.filtered(
                lambda att: not Profile._is_allowed_contract_file(att.name, mimetype=att.mimetype))
            if invalid:
                raise UserError(_('Chỉ chấp nhận file PDF hoặc ảnh. Các file không hợp lệ:\n%s')
                                % '\n'.join(invalid.mapped('name')))
            items = [(att.name, att) for att in self.th_attachment_ids]
        phone_items = {}
        unmatched = []
        for file_path, content in items:
            phone = self._extract_phone(file_path)
            if phone:
                phone_items.setdefault(phone, []).append((file_path, content))
            else:
                unmatched.append(file_path)

        Profile = self.env['th.collaborator.profile']
        profiles = Profile.search([('th_phone_normalized', 'in', list(phone_items))])
        profile_by_phone = {profile.th_phone_normalized: profile for profile in profiles}
        field_name = 'th_company_attachment_ids' if self.th_target_type == 'company' else 'th_self_attachment_ids'
        Attachment = self.env['ir.attachment']
        matched_count = 0
        for phone, phone_files in phone_items.items():
            profile = profile_by_phone.get(phone)
            if not profile:
                unmatched += [file_path for file_path, dummy in phone_files]
                continue
            attachments = Attachment
            for file_path, content in phone_files:
                if isinstance(content, models.BaseModel):
                    # Tái sử dụng file đã upload qua widget, tránh nhân đôi dữ liệu trên filestore
                    content.write({'res_model': profile._name, 'res_id': profile.id})
                    attachments |= content
                else:
                    attachments |= Attachment.create({
                        'name': os.path.basename(file_path),
                        'raw': content,
                        'res_model': profile._name,
                        'res_id': profile.id,
                    })
            profile.write({field_name: [Command.link(att.id) for att in attachments]})
            matched_count += len(attachments)

        # File upload qua widget mà không map được CTV sẽ thành rác trên filestore
        self.th_attachment_ids.filtered(lambda att: att.res_model == self._name).unlink()
        result = [_('Đã gắn %s file vào %s CTV.') % (matched_count, len(profiles))]
        if unmatched:
            result.append(_('Không map được %s file:') % len(unmatched))
            result += ['  - %s' % file_path for file_path in unmatched]
        self.write({
            'th_result_note': '\n'.join(result),
            'th_is_done': True,
            'th_zip_file': False,
        })
        _logger.info('Bulk contract import: %s file(s) matched, %s unmatched', matched_count, len(unmatched))
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
