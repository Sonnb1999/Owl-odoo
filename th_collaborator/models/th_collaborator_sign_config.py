# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class ThCollaboratorSignConfig(models.Model):
    """Cấu hình ký số hợp đồng, độc lập với nhà cung cấp chữ ký.

    Mỗi nhà cung cấp là 1 module riêng (vd th_collaborator_sign_vnpt) thêm giá trị vào
    th_provider bằng selection_add và override các hook bên dưới:
    - _get_provider_sign_mode(): 'client' (ký trên trình duyệt qua plugin/USB Token)
      hoặc 'server' (ký qua API từ xa)
    - _get_client_sign_options(): tuỳ chọn riêng của nhà cung cấp gửi xuống JS
    - _sign_pdf_server(): ký PDF phía server cho nhà cung cấp kiểu 'server'
    Phía JS, nhà cung cấp kiểu 'client' đăng ký vào registry "th_collaborator_sign_providers".
    """
    _name = 'th.collaborator.sign.config'
    _description = 'Cấu hình ký số hợp đồng'
    _order = 'sequence, id'

    name = fields.Char(string='Tên cấu hình')
    sequence = fields.Integer(string='Thứ tự', default=10)
    active = fields.Boolean(string='Đang sử dụng', default=True)
    th_provider = fields.Selection([], string='Nhà cung cấp chữ ký số')
    th_appearance_type = fields.Selection([
        ('description', 'Chỉ mô tả'),
        ('description_name', 'Mô tả + tên người ký'),
        ('description_image', 'Mô tả + ảnh'),
        ('image', 'Chỉ ảnh'),
        ('invisible', 'Ẩn (không hiển thị trên trang)'),
    ], string='Kiểu hiển thị chữ ký', default='description_image')
    th_image = fields.Binary(string='Ảnh con dấu/chữ ký')
    th_is_signer_visible = fields.Boolean(string='Hiện người ký', default=True)
    th_is_email_visible = fields.Boolean(string='Hiện email')
    th_is_position_visible = fields.Boolean(string='Hiện chức vụ')
    th_is_signing_time_visible = fields.Boolean(string='Hiện thời gian ký', default=True)
    th_description = fields.Text(string='Dòng mô tả tuỳ chỉnh')
    th_text_size = fields.Float(string='Cỡ chữ', default=8)
    th_text_color = fields.Char(string='Màu chữ')
    th_is_initial_all_pages = fields.Boolean(string='Ký nháy tất cả các trang')
    th_tsa_url = fields.Char(string='Địa chỉ TSA (dấu thời gian)')

    def _get_provider_sign_mode(self):
        """Kiểu ký của nhà cung cấp: 'client' hoặc 'server'. Module nhà cung cấp override."""
        self.ensure_one()
        return False

    def _get_client_sign_options(self):
        """Tuỳ chọn hiển thị chung gửi xuống JS; module nhà cung cấp bổ sung tuỳ chọn riêng."""
        self.ensure_one()
        return {
            'appearance_type': self.th_appearance_type,
            'image_base64': self.with_context(bin_size=False).th_image.decode() if self.th_image else False,
            'signer_visible': self.th_is_signer_visible,
            'email_visible': self.th_is_email_visible,
            'position_visible': self.th_is_position_visible,
            'signing_time_visible': self.th_is_signing_time_visible,
            'description': self.th_description or False,
            'text_size': self.th_text_size or 8,
            'text_color': self.th_text_color or False,
            'initial_all_pages': self.th_is_initial_all_pages,
            'tsa_url': self.th_tsa_url or False,
        }

    def _sign_pdf_server(self, pdf_data, sign_box, page_count):
        """Ký PDF phía server cho nhà cung cấp kiểu 'server'.

        :return: dict {'signed_pdf': bytes, 'cert_base64': str | False}
        """
        self.ensure_one()
        raise UserError(_('Nhà cung cấp "%s" chưa hỗ trợ ký phía server.') % (self.th_provider or ''))

