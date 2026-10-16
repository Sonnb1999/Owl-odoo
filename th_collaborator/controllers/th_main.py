# -*- coding: utf-8 -*-
import logging
import os
import re
import tempfile
import zipfile

from werkzeug.wsgi import wrap_file

from odoo import _, http
from odoo.http import content_disposition, request

from odoo.addons.th_collaborator.models.th_collaborator_profile import TH_CONTRACT_ALLOWED_EXTENSIONS

_logger = logging.getLogger(__name__)

TH_UPLOAD_MAX_FILES = 10
TH_UPLOAD_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB / file


class ThCollaboratorController(http.Controller):

    def _get_profile_by_token(self, token):
        """Tìm CTV theo token của link upload."""
        Profile = request.env['th.collaborator.profile']
        if not token or len(token) < 20:
            return Profile.browse()
        # sudo: CTV truy cập ẩn danh (public user) không có quyền đọc model;
        # chỉ tra đúng 1 bản ghi theo token ngẫu nhiên, không lộ dữ liệu khác.
        return Profile.sudo().search([('th_access_token', '=', token)], limit=1)

    def _render_upload_page(self, values):
        """Render trang upload hợp đồng công khai."""
        values.update({
            'th_max_files': TH_UPLOAD_MAX_FILES,
            'th_max_file_size_mb': TH_UPLOAD_MAX_FILE_SIZE // (1024 * 1024),
            'th_accept': ','.join(TH_CONTRACT_ALLOWED_EXTENSIONS),
        })
        return request.render('th_collaborator.th_collaborator_upload_page_template', values)

    def _read_uploaded_files(self):
        """Đọc và kiểm tra file CTV gửi lên; trả về (danh sách file, lỗi)."""
        storages = [f for f in request.httprequest.files.getlist('th_contract_files') if f.filename]
        if not storages:
            return [], _('Vui lòng chọn ít nhất 1 file hợp đồng.')
        if len(storages) > TH_UPLOAD_MAX_FILES:
            return [], _('Chỉ được tải tối đa %s file mỗi lần.') % TH_UPLOAD_MAX_FILES
        Profile = request.env['th.collaborator.profile']
        files = []
        for storage in storages:
            file_name = os.path.basename(storage.filename)
            # Đọc thêm 1 byte để phát hiện file vượt giới hạn mà không phải đọc hết
            content = storage.read(TH_UPLOAD_MAX_FILE_SIZE + 1)
            if len(content) > TH_UPLOAD_MAX_FILE_SIZE:
                return [], _('File "%s" vượt quá dung lượng cho phép.') % file_name
            if not Profile._is_allowed_contract_file(file_name, content=content):
                return [], _('File "%s" không hợp lệ, chỉ chấp nhận PDF hoặc ảnh.') % file_name
            files.append((file_name, content))
        return files, False

    @http.route('/th_collaborator/upload/<string:token>', type='http', auth='public', methods=['GET'])
    def render_upload_form(self, token, **kwargs):
        """Hiển thị form để CTV (không đăng nhập) tải hợp đồng lên."""
        if not self._get_profile_by_token(token):
            return request.not_found()
        return self._render_upload_page({'token': token, 'th_phone': ''})

    @http.route('/th_collaborator/upload/<string:token>/submit', type='http', auth='public', methods=['POST'])
    def submit_upload_form(self, token, th_phone=None, **kwargs):
        """Nhận hợp đồng CTV gửi lên, xác thực bằng SĐT đã đăng ký."""
        profile = self._get_profile_by_token(token)
        if not profile:
            return request.not_found()
        values = {'token': token, 'th_phone': th_phone or ''}
        if profile._normalize_phone(th_phone) != profile.th_phone_normalized:
            _logger.warning('Collaborator upload rejected: phone mismatch for profile %s', profile.id)
            values['error'] = _('Số điện thoại không khớp với thông tin đã đăng ký.')
            return self._render_upload_page(values)
        files, error = self._read_uploaded_files()
        if error:
            values['error'] = error
            return self._render_upload_page(values)
        profile._add_self_contracts(files)
        values['success'] = _('Xin chào %s, chúng tôi đã nhận %s file hợp đồng của bạn. Cảm ơn!') % (
            profile.name, len(files))
        return self._render_upload_page(values)

    def _write_attachment_to_zip(self, zip_file, attachment, arcname):
        """Ghi 1 attachment vào file ZIP, ưu tiên đọc thẳng từ filestore để tiết kiệm RAM."""
        if attachment.store_fname:
            full_path = attachment._full_path(attachment.store_fname)
            if os.path.isfile(full_path):
                zip_file.write(full_path, arcname)
                return
            _logger.warning('Attachment %s missing on filestore: %s', attachment.id, full_path)
        if attachment.raw:
            zip_file.writestr(arcname, attachment.raw)

    @http.route('/th_collaborator/contract/preview/<string:source>/<int:res_id>',
                type='http', auth='user', methods=['GET'])
    def preview_contract(self, source, res_id, **kwargs):
        """Xem trước hợp đồng đục lỗ ngay trên trình duyệt, không lưu file.

        source = 'profile': dữ liệu thật của CTV; source = 'template': dữ liệu mẫu.
        """
        models_by_source = {
            'profile': 'th.collaborator.profile',
            'template': 'th.collaborator.contract.template',
        }
        if source not in models_by_source:
            return request.not_found()
        record = request.env[models_by_source[source]].browse(res_id).exists()
        if not record:
            return request.not_found()
        record.check_access_rights('read')
        record.check_access_rule('read')
        if source == 'profile':
            template = record.th_contract_template_id
            if not template:
                return request.not_found()
            values = record._get_contract_field_values()
        else:
            template = record
            values = record._get_sample_field_values()
        pdf_data = template._render_filled_pdf(values)
        return request.make_response(pdf_data, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf_data)),
            ('Content-Disposition', 'inline; filename="preview.pdf"'),
        ])

    @http.route('/th_collaborator/download_zip', type='http', auth='user', methods=['GET'])
    def download_contract_zip(self, ids='', contract_type='company', **kwargs):
        """Tải 1 loại hợp đồng của nhiều CTV trong 1 file ZIP, mỗi CTV 1 thư mục (SĐT_Tên/file)."""
        if contract_type not in ('company', 'self'):
            return request.not_found()
        record_ids = [int(rec_id) for rec_id in ids.split(',') if rec_id.isdigit()]
        profiles = request.env['th.collaborator.profile'].browse(record_ids).exists()
        profiles.check_access_rights('read')
        profiles.check_access_rule('read')
        field_name = 'th_company_attachment_ids' if contract_type == 'company' else 'th_self_attachment_ids'

        # Ghi ZIP ra file tạm và stream về client để không giữ toàn bộ dữ liệu trong RAM
        tmp_file = tempfile.TemporaryFile()
        # ZIP_STORED: PDF/ảnh vốn đã nén, nén lại chỉ tốn CPU
        with zipfile.ZipFile(tmp_file, 'w', zipfile.ZIP_STORED, allowZip64=True) as zip_file:
            for profile in profiles:
                folder = re.sub(r'[\\/:*?"<>|]+', '_', '%s_%s' % (profile.th_phone_normalized or profile.id, profile.name or ''))
                used_names = set()
                for attachment in profile[field_name]:
                    file_name = re.sub(r'[\\/:*?"<>|]+', '_', attachment.name or str(attachment.id))
                    # Trùng tên file trong cùng thư mục thì thêm id để không bị ghi đè khi giải nén
                    if file_name.lower() in used_names:
                        stem, ext = os.path.splitext(file_name)
                        file_name = '%s_%s%s' % (stem, attachment.id, ext)
                    used_names.add(file_name.lower())
                    self._write_attachment_to_zip(zip_file, attachment, '%s/%s' % (folder, file_name))
        size = tmp_file.tell()
        tmp_file.seek(0)
        _logger.info('User %s downloaded %s contracts of %s collaborator(s)',
                     request.env.uid, contract_type, len(profiles))
        zip_name = 'hop_dong_cong_ty.zip' if contract_type == 'company' else 'hop_dong_ctv.zip'
        return http.Response(
            wrap_file(request.httprequest.environ, tmp_file),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Length', size),
                ('Content-Disposition', content_disposition(zip_name)),
            ],
            direct_passthrough=True,
        )
