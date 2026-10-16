# -*- coding: utf-8 -*-
import base64
import hashlib
import io
import logging
import os
import re

from PyPDF2.generic import ArrayObject, NameObject
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.pdf import PdfFileReader, PdfFileWriter

_logger = logging.getLogger(__name__)

# Gợi ý sẵn trường CTV khi ô form có tên quen thuộc; người dùng vẫn đổi được trên template
TH_PDF_SUGGESTED_FIELDS = {
    'ten': 'name',
    'ho_ten': 'name',
    'name': 'name',
    'email': 'th_email',
    'sdt': 'th_phone',
    'so_dien_thoai': 'th_phone',
    'phone': 'th_phone',
    'ten_hop_dong': 'th_contract_name',
    'loai_hop_dong': 'th_contract_type_ids',
}
# Font Unicode có đủ dấu tiếng Việt; ưu tiên cấu hình th_collaborator.pdf_font_path
TH_PDF_FONT_CANDIDATES = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    'C:/Windows/Fonts/arial.ttf',
    'C:/Windows/Fonts/times.ttf',
)
TH_PDF_DEFAULT_FONT_SIZE = 11
TH_PDF_MIN_FONT_SIZE = 5
TH_PDF_TEXT_PADDING = 2


class ThCollaboratorContractTemplate(models.Model):
    _name = 'th.collaborator.contract.template'
    _description = 'Template hợp đồng CTV'
    _order = 'sequence, id'

    def th_default_mail_template_id(self):
        """Mặc định dùng mẫu mail mời CTV tải hợp đồng của module."""
        return self.env.ref('th_collaborator.th_collaborator_profile_upload_mail_template', raise_if_not_found=False)

    name = fields.Char(string='Tên template')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang sử dụng', default=True)
    th_template_file = fields.Binary(string='File PDF template')
    th_template_filename = fields.Char(string='Tên file')
    th_detected_field_names = fields.Char(
        string='Ô form nhận diện được', compute='th_compute_detected_field_names', store=True)
    th_mail_template_id = fields.Many2one(
        'mail.template', string='Mẫu email', domain=[('model', '=', 'th.collaborator.profile')],
        default=lambda self: self.th_default_mail_template_id())
    th_contract_type_ids = fields.Many2many(
        'th.collaborator.contract.type', 'th_collaborator_contract_template_type_rel',
        'th_template_id', 'th_contract_type_id', string='Loại hợp đồng')
    th_field_line_ids = fields.One2many(
        'th.collaborator.contract.template.line', 'th_template_id', string='Cấu hình đục lỗ')

    @api.model_create_multi
    def create(self, vals_list):
        """Tạo template và tự sinh dòng cấu hình đục lỗ theo các ô form trong PDF."""
        records = super().create(vals_list)
        records._sync_field_lines()
        return records

    def write(self, vals):
        """Cập nhật template; đổi file PDF thì đồng bộ lại dòng cấu hình đục lỗ."""
        res = super().write(vals)
        if 'th_template_file' in vals:
            self._sync_field_lines()
        return res

    def _sync_field_lines(self):
        """Đồng bộ dòng cấu hình với ô form trong PDF: thêm ô mới, bỏ ô không còn, giữ cấu hình cũ.

        Ô vẽ tay trên màn hình thiết kế không phụ thuộc ô form nên không bị đồng bộ.
        """
        for rec in self.filtered('th_template_file'):
            pdf_names = self._read_pdf_field_names(rec._get_template_pdf_data())
            form_lines = rec.th_field_line_ids.filtered(lambda line: not line.th_is_manual)
            existing_names = set(rec.th_field_line_ids.mapped('th_pdf_field_name'))
            form_lines.filtered(lambda line: line.th_pdf_field_name not in pdf_names).unlink()
            new_lines = []
            for sequence, pdf_name in enumerate(pdf_names, start=1):
                if pdf_name in existing_names:
                    continue
                suggested = TH_PDF_SUGGESTED_FIELDS.get(pdf_name)
                new_lines.append({
                    'th_template_id': rec.id,
                    'sequence': sequence,
                    'th_pdf_field_name': pdf_name,
                    'th_field_name': suggested or False,
                })
            if new_lines:
                self.env['th.collaborator.contract.template.line'].create(new_lines)

    def th_action_sync_field_lines(self):
        """Đọc lại ô form trong PDF để cập nhật bảng cấu hình đục lỗ."""
        self.ensure_one()
        self._get_template_pdf_data()
        self._sync_field_lines()
        return True

    def _get_field_values(self, record):
        """Giá trị điền vào từng ô form theo cấu hình đục lỗ, lấy từ bản ghi CTV."""
        self.ensure_one()
        return {
            line.th_pdf_field_name: line._format_field_value(record)
            for line in self.th_field_line_ids if line.th_field_name
        }

    def _get_sample_field_values(self):
        """Giá trị mẫu (nhãn trường) để xem thử vị trí đục lỗ trên template."""
        self.ensure_one()
        return {
            line.th_pdf_field_name: line._get_sample_value()
            for line in self.th_field_line_ids if line.th_field_name
        }

    def _get_template_pdf_data(self):
        """Đọc nội dung bytes của file PDF template."""
        self.ensure_one()
        data = self.with_context(bin_size=False).th_template_file
        if not data:
            raise UserError(_('Template "%s" chưa có file PDF.') % self.name)
        return base64.b64decode(data)

    @api.model
    def _get_widget_name(self, annot):
        """Lấy tên ô form (viết thường) của 1 widget, tên có thể nằm ở widget hoặc field cha."""
        name = annot.get('/T')
        if name is None and annot.get('/Parent') is not None:
            name = annot['/Parent'].getObject().get('/T')
        return str(name).strip().lower() if name is not None else False

    @api.model
    def _iter_pdf_widgets(self, reader):
        """Duyệt các ô form (widget) trong PDF, trả về (số trang, widget, tên ô)."""
        for page_index in range(reader.getNumPages()):
            page = reader.getPage(page_index)
            for annot_ref in page.get('/Annots') or []:
                annot = annot_ref.getObject()
                if annot.get('/Subtype') == '/Widget':
                    yield page_index, annot, self._get_widget_name(annot)

    @api.model
    def _read_pdf_field_names(self, pdf_data):
        """Trả về danh sách tên ô form có trong PDF."""
        reader = PdfFileReader(io.BytesIO(pdf_data), strict=False)
        if reader.isEncrypted:
            raise UserError(_('File PDF đang bị đặt mật khẩu, vui lòng bỏ mật khẩu trước khi tải lên.'))
        return sorted({name for dummy, dummy2, name in self._iter_pdf_widgets(reader) if name})

    @api.depends('th_template_file')
    def th_compute_detected_field_names(self):
        """Hiển thị các ô form có trong template để người dùng kiểm tra việc đục lỗ."""
        for rec in self:
            names = []
            data = rec.with_context(bin_size=False).th_template_file
            if data:
                try:
                    names = self._read_pdf_field_names(base64.b64decode(data))
                except Exception:
                    # File lỗi sẽ được th_check_template_file báo cho người dùng
                    _logger.warning('Cannot read form fields of contract template %s', rec.id, exc_info=True)
            rec.th_detected_field_names = ', '.join(names) or False

    @api.constrains('th_template_file')
    def th_check_template_file(self):
        """Kiểm tra template là PDF đọc được (có hoặc không có ô form đều được)."""
        for rec in self:
            if not rec.th_template_file:
                continue
            pdf_data = rec._get_template_pdf_data()
            if guess_mimetype(pdf_data) != 'application/pdf':
                raise ValidationError(_('Template hợp đồng phải là file PDF.'))
            self._read_pdf_field_names(pdf_data)

    @api.model
    def _get_pdf_font_name(self):
        """Đăng ký font Unicode cho reportlab và trả về tên font để vẽ chữ tiếng Việt."""
        # sudo: người dùng nội bộ không có quyền đọc ir.config_parameter, chỉ đọc 1 key cấu hình font
        configured_path = self.env['ir.config_parameter'].sudo().get_param('th_collaborator.pdf_font_path')
        candidates = ([configured_path] if configured_path else []) + list(TH_PDF_FONT_CANDIDATES)
        font_path = next((path for path in candidates if path and os.path.isfile(path)), False)
        if not font_path:
            raise UserError(_(
                'Không tìm thấy font tiếng Việt trên server. Cài gói fonts-dejavu hoặc khai báo '
                'đường dẫn file .ttf vào tham số hệ thống "th_collaborator.pdf_font_path".'))
        font_name = 'ThContract_%s' % hashlib.md5(font_path.encode()).hexdigest()[:8]
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        return font_name

    @api.model
    def _get_widget_font_size(self, annot):
        """Lấy cỡ chữ khai báo của ô form (/DA); 0 nghĩa là tự động."""
        appearance = annot.get('/DA')
        if appearance is None and annot.get('/Parent') is not None:
            appearance = annot['/Parent'].getObject().get('/DA')
        match = re.search(r'(\d+(?:\.\d+)?)\s+Tf', str(appearance or ''))
        return float(match.group(1)) if match else 0

    @api.model
    def _build_overlay_page(self, page, boxes, font_name):
        """Vẽ chữ vào các ô trên 1 trang, trả về trang overlay để ghép.

        :param boxes: list dict {'rect': (x1, y1, x2, y2), 'font_size': float (0 = tự động), 'text': str}
        """
        packet = io.BytesIO()
        pdf_canvas = canvas.Canvas(packet, pagesize=(
            float(page.mediaBox.getUpperRight_x()), float(page.mediaBox.getUpperRight_y())))
        for box in boxes:
            text = box['text']
            if not text:
                continue
            x1, y1, x2, y2 = box['rect']
            x1, x2 = sorted((x1, x2))
            y1, y2 = sorted((y1, y2))
            font_size = box['font_size'] or min((y2 - y1) * 0.7, TH_PDF_DEFAULT_FONT_SIZE)
            max_width = x2 - x1 - 2 * TH_PDF_TEXT_PADDING
            # Thu nhỏ chữ cho vừa ô thay vì để chữ tràn ra ngoài
            while font_size > TH_PDF_MIN_FONT_SIZE and pdfmetrics.stringWidth(text, font_name, font_size) > max_width:
                font_size -= 0.5
            pdf_canvas.setFont(font_name, font_size)
            baseline = y1 + (y2 - y1 - font_size) / 2 + font_size * 0.2
            pdf_canvas.drawString(x1 + TH_PDF_TEXT_PADDING, baseline, text)
        pdf_canvas.showPage()
        pdf_canvas.save()
        packet.seek(0)
        return PdfFileReader(packet, strict=False).getPage(0)

    def _render_filled_pdf(self, values):
        """Đục lỗ template: điền giá trị vào các ô form và làm phẳng (flatten) PDF.

        Chữ được vẽ trực tiếp bằng font Unicode thay vì điền vào ô form, để tiếng Việt
        hiển thị đúng trên mọi trình đọc PDF và CTV không sửa được nội dung đã điền.

        :param values: dict {tên ô form viết thường: giá trị}
        :return: bytes của file PDF đã điền
        """
        self.ensure_one()
        font_name = self._get_pdf_font_name()
        reader = PdfFileReader(io.BytesIO(self._get_template_pdf_data()), strict=False)
        boxes_by_page = {}
        filled_widget_ids = set()
        manual_names = set(self.th_field_line_ids.filtered('th_is_manual').mapped('th_pdf_field_name'))
        # Ô form có sẵn trong PDF
        for page_index, annot, name in self._iter_pdf_widgets(reader):
            if name in values and name not in manual_names:
                filled_widget_ids.add(id(annot))
                boxes_by_page.setdefault(page_index, []).append({
                    'rect': tuple(float(value) for value in annot['/Rect']),
                    'font_size': self._get_widget_font_size(annot),
                    'text': values[name],
                })
        # Ô vẽ tay trên màn hình thiết kế
        for line in self.th_field_line_ids.filtered('th_is_manual'):
            if line.th_pdf_field_name in values and 1 <= line.th_page <= reader.getNumPages():
                boxes_by_page.setdefault(line.th_page - 1, []).append({
                    'rect': (line.th_pos_x, line.th_pos_y,
                             line.th_pos_x + line.th_width, line.th_pos_y + line.th_height),
                    'font_size': line.th_font_size,
                    'text': values[line.th_pdf_field_name],
                })

        writer = PdfFileWriter()
        for page_index in range(reader.getNumPages()):
            page = reader.getPage(page_index)
            boxes = boxes_by_page.get(page_index)
            if boxes:
                if filled_widget_ids and page.get('/Annots'):
                    # Bỏ các ô form đã điền khỏi trang để không còn ô trống đè lên chữ đã vẽ
                    kept_annots = [ref for ref in page['/Annots'] if id(ref.getObject()) not in filled_widget_ids]
                    if kept_annots:
                        page[NameObject('/Annots')] = ArrayObject(kept_annots)
                    else:
                        del page['/Annots']
                page.mergePage(self._build_overlay_page(page, boxes, font_name))
            writer.addPage(page)
        with io.BytesIO() as buffer:
            writer.write(buffer)
            return buffer.getvalue()

    def th_action_open_designer(self):
        """Mở màn hình thiết kế để vẽ ô đục lỗ trực tiếp lên PDF."""
        self.ensure_one()
        self._get_template_pdf_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'th_collaborator.contract_template_designer',
            'name': _('Thiết kế ô đục lỗ: %s') % self.name,
            'params': {'template_id': self.id},
        }

    def th_get_designer_data(self):
        """Dữ liệu cho màn hình thiết kế: link PDF, danh sách trường CTV, các ô vẽ tay đã lưu."""
        self.ensure_one()
        Line = self.env['th.collaborator.contract.template.line']
        return {
            'name': self.name,
            'pdf_url': '/web/content/%s/%s/th_template_file' % (self._name, self.id),
            'field_options': Line._get_mappable_field_selection(),
            'boxes': [{
                'id': line.id,
                'page': line.th_page,
                'x': line.th_pos_x,
                'y': line.th_pos_y,
                'width': line.th_width,
                'height': line.th_height,
                'font_size': line.th_font_size,
                'field_name': line.th_field_name or False,
            } for line in self.th_field_line_ids.filtered('th_is_manual')],
        }

    def th_save_designer_boxes(self, boxes):
        """Lưu các ô vẽ tay từ màn hình thiết kế: cập nhật ô cũ, tạo ô mới, xoá ô đã bỏ.

        :param boxes: list dict {id, page, x, y, width, height, font_size, field_name}
        """
        self.ensure_one()
        Line = self.env['th.collaborator.contract.template.line']
        valid_fields = dict(Line._get_mappable_field_selection())
        manual_lines = self.th_field_line_ids.filtered('th_is_manual')
        used_names = set(self.th_field_line_ids.mapped('th_pdf_field_name'))
        kept_ids = set()
        new_vals = []
        for index, box in enumerate(boxes, start=1):
            field_name = box.get('field_name')
            if field_name and field_name not in valid_fields:
                raise UserError(_('Trường "%s" không được phép đục lỗ.') % field_name)
            vals = {
                'th_page': int(box.get('page') or 1),
                'th_pos_x': float(box.get('x') or 0),
                'th_pos_y': float(box.get('y') or 0),
                'th_width': max(float(box.get('width') or 0), 1),
                'th_height': max(float(box.get('height') or 0), 1),
                'th_font_size': max(float(box.get('font_size') or 0), 0),
                'th_field_name': field_name or False,
                'sequence': 100 + index,
            }
            line = manual_lines.filtered(lambda rec: rec.id == box.get('id'))
            if line:
                line.write(vals)
                kept_ids.add(line.id)
                continue
            # Ô vẽ tay không có tên trong PDF nên tự sinh khoá riêng, không trùng ô form
            sequence_number = len(used_names) + 1
            while 'manual_%s' % sequence_number in used_names:
                sequence_number += 1
            pdf_name = 'manual_%s' % sequence_number
            used_names.add(pdf_name)
            new_vals.append(dict(vals, th_template_id=self.id, th_is_manual=True, th_pdf_field_name=pdf_name))
        manual_lines.filtered(lambda rec: rec.id not in kept_ids).unlink()
        if new_vals:
            Line.create(new_vals)
        _logger.info('Contract template %s: saved %s manual box(es)', self.id, len(boxes))
        return True

    def th_action_preview_template(self):
        """Xem thử template sau khi đục lỗ với dữ liệu mẫu."""
        self.ensure_one()
        self._get_template_pdf_data()
        return {
            'type': 'ir.actions.act_url',
            'url': '/th_collaborator/contract/preview/template/%s' % self.id,
            'target': 'new',
        }
