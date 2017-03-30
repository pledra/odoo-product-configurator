# -*- coding: utf-8 -*-
{
    'name': 'Product Configurator Wizard',
    'version': '10.0.1.0.0',
    'category': 'Generic Modules/Base',
    'summary': 'Back-end Product Configurator',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['sale', 'product_configurator'],
    "data": [
        'wizard/product_configurator_view.xml',
        'views/assets.xml',
        'views/sale_view.xml',
    ],
    'images': [
        'static/description/cover.png'
    ],
    'installable': True,
    'auto_install': False,
}
