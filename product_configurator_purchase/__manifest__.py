# -*- coding: utf-8 -*-

{
    'name': 'Product Configurator Purchase',
    'version': '10.0',
    'category': 'Generic Modules/Base',
    'summary': 'product configuration interface for purchase',
    'description': """
        Purchase Product Configurator
    """,
    'author': 'Microcom',
    'license': 'AGPL-3',
    'website': 'http://www.microcom.ca/',
    'depends': [
        'purchase',
        'product_configurator',
        'product_configurator_wizard',
    ],
    "data": [
        'views/purchase_views.xml',
        'views/stock_picking_views.xml',
    ],
    'demo': [
    ],
    'images': [
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
