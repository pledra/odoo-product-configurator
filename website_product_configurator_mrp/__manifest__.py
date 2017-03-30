# -*- coding: utf-8 -*-
{
    'name': 'Website Configurator Manufacturing',
    'version': '10.0.1.0.0',
    'category': 'Website',
    'summary': 'Website integration of MRP',
    'author': 'Pledra',  # pylint: disable=C8101
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
