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
        'url',
    ],
    'data': [
    ],

    'qweb': [
    ],
    'assets': {
        'web.assets_backend': [
            # 'js_widget/static/src/xml/url_widget.xml'
            'js_widget/static/src/js/url_widget.js'
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
