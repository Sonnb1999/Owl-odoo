# -*- coding: utf-8 -*-
{
    'name': 'TH Collaborator - Ký số VNPT-CA Plugin',
    'summary': 'Ký số hợp đồng CTV bằng USB Token qua VNPT-CA Plugin',
    'author': 'Sonbn',
    'version': '16.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'Human Resources',
    'depends': ['th_collaborator'],
    'data': [
        'views/th_collaborator_sign_config_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'th_collaborator_sign_vnpt/static/src/js/th_vnpt_sign_provider.js',
        ],
    },
    'installable': True,
    'auto_install': False,
}
