# -*- coding: utf-8 -*-
{
    'name': 'ABS Portal',
    'author': "TH Company",
    'summary': 'ABS Portal',
    'category': 'AUM Business System/ Portal',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'contacts',
        'portal',
        'mail',
        'website',
        'website_blog',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/link_tracker_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/th_attachment_view.xml',
        'views/menu.xml',

        'views/portal_templates.xml',
        'views/portal_student_info_template.xml',
        'views/th_template_application_forms.xml',
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
