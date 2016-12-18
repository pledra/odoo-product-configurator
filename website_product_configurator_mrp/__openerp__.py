# -*- coding: utf-8 -*-
{
    'name': 'Website Configurator Manufacturing',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Website integration of MRP',
    'description': """Adds MRP logic to configurable products in frontend""",
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': [
        'product_configurator_mrp',
        'website_product_configurator',
    ],
    'data': ['templates.xml'],
    'installable': True,
    'auto_install': False,
}
