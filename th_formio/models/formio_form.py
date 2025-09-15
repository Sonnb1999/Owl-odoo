import json

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
import xmlrpc.client
from datetime import timedelta

class Form(models.Model):
    _inherit = 'formio.form'

    th_submission_data = fields.Html('Data', default=False)
    th_state_data = fields.Selection(selection=[('fake', 'Dữ liệu thử'), ('real', 'Dữ liệu thật')], string='Dữ liệu là', default=False)
    th_error_form = fields.Text('Lỗi form')
    th_ownership_unit_id = fields.Many2one('th.ownership.unit', string='Đơn vị sở hữu')
    th_sambala_pushed = fields.Boolean('Đã đẩy sang Sambala', default=False)
    th_sambala_push_error = fields.Text('Dữ liệu bị đẩy lỗi')
    th_sambala_value = fields.Char('Dữ liệu bị đẩy lỗi')
    th_sambala_context = fields.Char('Context')
    # def unlink(self):
    #     for rec in self:
    #         if rec.th_state_data == 'real':
    #             raise ValidationError('Bạn ko có quyền xoá các dữ liệu trên.')
    #     return super(Form, self).unlink()

    def th_get_form_to_push(self):
        """
        Lấy dữ liệu form để đẩy sang Sambala
        """
        forms = self.search([('th_sambala_pushed', '=', False)], order='create_date asc')
        
        if not forms:
            return
            
        # Xử lý từng form
        for form in forms:
            if form.th_state_data == 'real':
                try:
                    # Xác định context dựa vào loại storage của form
                    storage_type = form.builder_id.th_storage_location
                    if storage_type not in ['crm', 'prm', 'apm']:
                        form.th_sambala_push_error = 'Không tìm thấy cấu hình để đẩy dữ liệu!'
                        form.th_sambala_pushed = True
                        continue
                    # Gán context 2 trường để tìm kiếm đơn vị sở hữu và form
                    context = json.loads(form.th_sambala_context)
                    # Tìm server API
                    server_api = request.env['th.api.server'].search([
                        ('state', '=', 'deploy'), 
                        ('th_type', '=', 'samp')
                    ], limit=1, order='id desc')
                    
                    if not server_api:
                        form.th_sambala_push_error = 'Lỗi hệ thống do không tìm thấy server!'
                        form.th_sambala_pushed = True
                        continue
                    
                    # Kết nối và gọi API
                    result_apis = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(server_api.th_url_api), allow_none = True)
                    db = server_api.th_db_api
                    uid_api = server_api.th_uid_api
                    password = server_api.th_password
                    
                    # Lấy dữ liệu từ formio_form
                    values = json.loads(form.th_sambala_value)
                    
                    # Xác định model dựa vào storage_type
                    model_mapping = {
                        'crm': 'crm.lead',
                        'prm': 'prm.lead',
                        'apm': 'th.apm'
                    }
                    model_name = model_mapping.get(storage_type)
                    
                    if not model_name:
                        form.th_sambala_push_error = 'Không tìm thấy model tương ứng với storage type!'
                        continue
                    
                    result_apis.execute_kw(
                        db, uid_api, password, 
                        model_name, 'create_lead_aff', 
                        [[], values], 
                        {'context': context}
                    )
                    
                    # Đánh dấu đã xử lý thành công
                    form.th_sambala_pushed = True
                    
                except Exception as e:
                    form.th_sambala_push_error = str(e)
                    
    def th_clean_old_pushed_forms(self):
        """
        Xóa các dữ liệu form cũ đã được đẩy về Sambala (trên 90 ngày)
        """
        # Tính ngày cách đây 90 ngày
        ninety_days_ago = fields.Datetime.now() - timedelta(days=90)
        
        # Tìm các form thỏa mãn điều kiện
        old_forms = self.search([
            ('create_date', '<', ninety_days_ago),
            ('th_sambala_pushed', '=', True)
        ])
        
        if old_forms:
            # Xóa các form
            old_forms.unlink()
        else:
            raise ValidationError(_('Không có dữ liệu form nào để xóa.'))
