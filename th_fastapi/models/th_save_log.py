# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class ThSaveLog(models.Model):
    """
    Lưu thông tin được đẩy về
    """

    _name = "th.save.log"
    _description = "Save log"

    name = fields.Char('Tên')
    th_url = fields.Char('Địa chỉ trang web')
    th_fastapi_id = fields.Many2one('fastapi.endpoint')
    th_data_response = fields.Text('Dữ liệu')
    th_date_response = fields.Datetime('Ngày', default=fields.Datetime.now)
    th_state = fields.Selection([('success', 'Thành công'), ('lost', 'Thất bại')], default='success')
