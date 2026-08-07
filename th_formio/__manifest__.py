{
    'name': 'ABS Formio',
    'author': "AUM Company",
    'summary': 'ABS Formio',
    'category': 'AUM Business System/ Formio',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'version': '16.0.0.1.120925',
    'depends': [
        'formio',
        'th_setup_parameters'
    ],
    'data': [
        'data/th_data_translate.xml',
        'security/ir.model.access.csv',
        'security/ir_model_access.xml',
        'security/security.xml',
        'security/ir_rule.xml',
        'views/th_partner_website.xml',
        'views/th_translate.xml',
        'views/th_custom_view_formio.xml',
        'views/formio_builder_views.xml',
        'views/formio_public_templates.xml',
        'views/th_res_config_settings_views.xml',
        'views/formio_menu.xml',
        'views/formio_form_views.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'th_formio/static/src/js/form/formio_form.js',
        ],
    },
    'installable': True,
    'application': True,
}
