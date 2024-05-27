# -*- coding: utf-8 -*-
{
    'name': 'ABS portal',
    'author': "TH Company",
    'summary': 'ABS Affiliate',
    'category': 'AUM Business System/ portal',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'portal',
        'mail',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/link_tracker_security.xml',
        'security/ir.model.access.csv',
        'views/th_student_info_view.xml',
        'views/menu.xml',
        'views/portal_templates.xml',
        'views/portal_own_links_template.xml',
        'views/portal_student_info_template.xml',
        'views/th_student_info_view.xml',
        'views/portal_own_port_links_template.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            # 'th_portal_student/static/src/scss/main.scss'
        ],
        'web.assets_backend': [
            # 'th_portal_student/static/src/scss/main.scss'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
