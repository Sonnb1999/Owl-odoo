# -*- coding: utf-8 -*-
{
    'name': 'TH Collaborator',
    'summary': 'Quản lý thông tin và hợp đồng cộng tác viên (CTV)',
    'author': 'Sonbn',
    'version': '16.0.1.1.0',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['mail'],
    'data': [
        'security/th_collaborator_groups.xml',
        'security/ir.model.access.csv',
        'data/th_collaborator_mail_template_data.xml',
        'views/th_collaborator_profile_views.xml',
        'views/th_collaborator_upload_templates.xml',
        'wizard/th_collaborator_upload_wizard_views.xml',
        'views/th_collaborator_menus.xml',
    ],
    'installable': True,
    'application': True,
}
