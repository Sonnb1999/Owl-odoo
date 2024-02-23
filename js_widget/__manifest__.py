# -*- coding: utf-8 -*-
{
    'name': 'ABS widget',
    'author': "TH Company",
    'summary': 'ABS widget',
    'category': 'AUM Business System/ widget',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
    ],

    'qweb': [
    ],
    'assets': {
        'web.assets_backend': [
            # 'js_widget/static/src/xml/url_widget.xml',
            'js_widget/static/src/js/chatter.js',
            'js_widget/static/src/xml/chatter_topbar.xml',
            'js_widget/static/src/xml/message_list.xml',
            'js_widget/static/src/js/thread_cache.js'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
