import base64
import uuid

from odoo import tools, models, fields, api, _, modules
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    th_student_code = fields.Char(string="Mã sinh viên", copy=False)
