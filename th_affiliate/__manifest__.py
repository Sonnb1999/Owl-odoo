# -*- coding: utf-8 -*-
{
    'name': 'ABS Affiliate',
    'author': "TH Company",
    'summary': 'ABS Affiliate',
    'category': 'AUM Business System/ Affiliate',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'link_tracker',
        'portal',
        'mail',
        'th_contact',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/link_tracker_security.xml',
        'security/ir.model.access.csv',
        'views/th_link_seeding.xml',
        'views/link_tracker_views.xml',
        'views/seeding_acceptance.xml',
        'views/res_config_settings_views.xml',
        'views/th_aff_ownership_unit.xml',
        'views/utm.xml',
        'views/th_product_aff_category.xml',
        'views/th_product_aff.xml',
        'views/th_pay.xml',
        'views/th_post_link.xml',
        'views/th_session_user.xml',
        'views/menus.xml',

        'views/portal_templates.xml',
        'views/portal_own_links_template.xml',
        'views/portal_link_seeding_template.xml',
        'views/portal_create_link_seeding.xml',
        'views/portal_own_port_links_template.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            # 'th_affiliate/static/src/scss/main.scss'
        ],
        'web.assets_backend': [
            # 'th_affiliate/static/src/scss/main.scss'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
