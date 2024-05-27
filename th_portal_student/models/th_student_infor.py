import base64
import uuid

from odoo import tools, models, fields, api, _, modules
from collections import defaultdict
from odoo.exceptions import ValidationError
from odoo.modules import get_module_resource


class StudentInfo(models.Model):
    _name = 'th.student.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Tên')
    th_age = fields.Char('Tuổi')
    th_address = fields.Char('Địa chỉ')
