# -*- coding: utf-8 -*-
{
    'name': "form_readonly",
    'summary': "Form readonly module",
    'description': """
        Set the readonly attribute of the form based on the readonly_domain field of the model.
    """,
    'author': "AUM",
    'license': 'AGPL-3',
    'category': 'Custom/Custom',
    'version': '16.0.1.0.0',
    'depends': ['base', 'web'],
    'assets': {
        'web.assets_backend': [
            'form_readonly/static/src/js/form_controller.js',
            'form_readonly/static/src/js/form_renderer.js',
        ]
    },
    'installable': True,
}
