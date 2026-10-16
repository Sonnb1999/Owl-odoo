# -*- coding: utf-8 -*-
{
    'name': 'TH Collaborator',
    'summary': 'Quản lý thông tin và hợp đồng cộng tác viên (CTV)',
    'author': 'Sonbn',
    'version': '16.0.1.3.0',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['mail'],
    'data': [
        'security/th_collaborator_groups.xml',
        'security/ir.model.access.csv',
        'data/th_collaborator_mail_template_data.xml',
        'views/th_collaborator_contract_type_views.xml',
        'views/th_collaborator_sign_config_views.xml',
        'views/th_collaborator_contract_template_views.xml',
        'views/th_collaborator_profile_views.xml',
        'views/th_collaborator_upload_templates.xml',
        'wizard/th_collaborator_upload_wizard_views.xml',
        'views/th_collaborator_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'th_collaborator/static/src/js/th_contract_template_designer.js',
            'th_collaborator/static/src/js/th_contract_sign_action.js',
            'th_collaborator/static/src/xml/th_contract_template_designer.xml',
            'th_collaborator/static/src/scss/th_contract_template_designer.scss',
        ],
    },
    'installable': True,
    'application': True,
}
