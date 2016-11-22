# -*- coding: utf-8 -*-
{
    'name': 'Product Configurator Wizard',
    'version': '1.0',
    'category': 'Generic Modules/Base',
    'summary': 'Back-end Product Configurator',
    'description': """
        This module provides a backend configuration wizard for generating
        products directly from any Odoo standard model such as Sale Order,
        Production Order etc.

        The view is dynamically generated using the information provided
        on the configurable template.
    """,
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['sale', 'product_configurator'],
    "data": [
        'wizard/product_configurator_view.xml',
        'views/assets.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
