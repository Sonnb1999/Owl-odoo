{
    'name': 'ABS CRM LIVECHAT',
    'author': "TH Company",
    'summary': 'ABS CRM LIVECHAT',
    'category': 'AUM Business System/ CRM LIVECHAT',
    'website': 'https://aum.edu.vn/',
    'license': 'LGPL-3',
    'depends': [
        'crm_livechat',
        "mail",
    ],
    'data': [
        'views/chat_bot_script_step.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'assets': {
        # 'web.assets_backend': [
        #     'th_stock/static/src/xml/view_button_help.xml',
        # ],
        'im_livechat.assets_public_livechat': [
            'th_crm_livechat/static/src/public_models/*.js',
            # 'website_livechat/static/src/legacy/widgets/*/*',
        ],
        'web.assets_frontend': [
            # 'th_crm_livechat/static/src/public_models/chatbot.js',
        ],

        'im_livechat.external_lib': [

        ]
    },
}
