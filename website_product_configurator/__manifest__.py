# -*- coding: utf-8 -*-
{
    'name': "Website Product Configurator",
    'version': '10.0.1.0.0',
    'summary': """Configure products in e-shop""",
    'author': "Pledra",
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'category': 'website',

    'depends': ['website_sale', 'product_configurator'],

    'data': [
        'security/ir.model.access.csv',
        'data/config_layout.xml',
        'views/product_config_view.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/product_template.xml',
        'demo/product_config_step.xml'
    ],
    'images': [
        'static/description/cover.png'
    ],
    'application': True
}
