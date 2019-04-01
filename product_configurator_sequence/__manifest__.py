{
    'name': 'Product Configurator Sequence',
    'version': '11.0.1.0.0',
    'category': 'Generic Modules/Base',
    'summary': 'Build images image dynamically from configuration',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['product_configurator', 'product_configurator_image_builder'],
    "data": [
        'views/product_view.xml',
        'views/product_attribute_view.xml',
        'wizard/product_attribute_wizard_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
