# -*- coding: utf-8 -*-
{
    'name': "Payment Wompi Module",
    'summary': "Wompi implementation",
    'description': """
        Wompi implementation
    """,
    'author': "Saul Morales Pacheco",
    'website': "https://www.saulmoralespa.com",
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Providers',
    'version': '1.0.0',
    'depends': ['payment'],
    'data': [
        'views/payment_wompi_templates.xml',
        'views/payment_views.xml',
        'data/payment_provider_data.xml',
    ],
    'application': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook'
}
