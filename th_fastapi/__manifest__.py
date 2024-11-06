# -*- coding: utf-8 -*-
{
    'name': 'ABS FastAPI',
    'author': "TH Company",
    'summary': 'ABS widget',
    'category': 'AUM Business System/ Odoo FastAPI',
    "website": "https://github.com/OCA/rest-framework",
    "version": "16.0.0.1.240824.1",
    'license': 'LGPL-3',
    'depends': [
        'fastapi',
        'base_automation',
    ],
    'data': [
        'data/data_test.xml',
        "security/ir.model.access.csv",
        "views/fastapi_menu.xml",
        "views/fastapi_endpoint_curd.xml",
    ],

    'qweb': [],

    'installable': True,
    'application': True,
    'auto_install': False,
}
