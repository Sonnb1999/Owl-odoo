# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError


class OdooIn(models.Model):
    _name = 'th.intermediate.table'

    def th_function_create(self, data=None, model=None, **kwargs):
        try:
            vals = {
                'name': 'tạo file',
                'nodel': model,
                'th_data': data,
                'th_method': 'create'
                'th_type'
            }
            if data:
                self.env['th.odoo.log'].create(data)
        except ValidationError as e:
            raise ValidationError(e)

    def th_function_update(self, data=None):
        try:
            raise ValidationError('This field is required.')
        except ValidationError as e:
            raise ValidationError(e)

    def th_function_delete(self, data=None):
        try:
            raise ValidationError('This field is required.')
        except ValidationError as e:
            raise ValidationError(e)

    def th_function_get(self, data=None):
        return self



