# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class ThAccessUrl(models.Model):
    """
    Chấp thuận các website được phép truy cập vào tài nguyên thông qua API
    """

    _name = "th.access.url"
    _description = "Chấp thuận cors"

    name = fields.Char('Tên')
    th_url = fields.Char('Địa chỉ trang web')
    th_is_access = fields.Boolean('Được chấp thuận')
    th_fastapi_id = fields.Many2one('fastapi.endpoint')
