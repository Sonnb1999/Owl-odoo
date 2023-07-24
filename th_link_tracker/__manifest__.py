# -*- coding: utf-8 -*-
{
    'name': 'ABS Link Tracking',
    'author': "TH Company",
    'summary': 'ABS Link Tracking',
    'category': 'AUM Business System/ Link Tracking',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'link_tracker',
        'portal',
        'mail',
        'th_contact',
    ],
    'data': [
        'security/link_tracker_security.xml',
        'security/ir.model.access.csv',
        'views/th_link_seeding.xml',
        'views/portal_templates.xml',
        'views/portal_own_links_template.xml',
        'views/portal_link_seeding_template.xml',
        'views/portal_own_port_links_template.xml',
        'views/link_tracker_views.xml',
        'views/seeding_acceptance.xml',
        'views/res_config_settings_views.xml',
        'views/menus.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            # 'th_link_tracker/static/src/scss/main.scss'
        ],
        'web.assets_backend': [
            # 'th_link_tracker/static/src/scss/main.scss'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
