# -*- coding: utf-8 -*-
{
    'name': 'Product Configurator Sale',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Sale',
    'summary': 'product configuration interface modules for Sale',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['sale_stock', 'product_configurator'],
    "data": [
        'views/sale_view.xml',
    ],
    'demo': [
        'demo/product_template.xml'
    ],
    'images': [
        'static/description/cover.png'
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
