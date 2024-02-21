# -*- coding: utf-8 -*-
{
    'name': 'TH Pagoda',
    'website': 'https://www.facebook.com/dev.Phuong2711/',
    'summary': 'Pagoda online',
    'author': 'Sonbn',
    'version': '16.0.1.2',
    'license': 'LGPL-3',
    'support ': 'Dev.Phuong2711@gmail.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/car_sequence.xml',
        'views/th_car_view.xml',
        'views/th_automobile_company_view.xml',
        'views/menu.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'th_pagoda/static/src/js/*.js',
            'th_pagoda/static/src/xml/*.xml',
            'th_pagoda/static/src/scss/*.scss',
        ],
    },
    'installable': True,
    'application': True,
}