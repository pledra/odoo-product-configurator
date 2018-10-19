{
    'name': 'Product Configurator Subconfiguration',
    'version': '11.0.1.0.1',
    'category': 'Generic Modules/Base',
    'summary': 'Allow configuration of multiple products within one template ',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['product_configurator', ],
    "data": [
        'security/ir.model.access.csv',
        'views/product_config_view.xml',
        'views/product_view.xml',
    ],
    'demo': [
    ],
    'images': [
        'static/description/cover.png'
    ],
    'qweb': ['static/xml/create_button.xml'],
    'test': [],
    'installable': False,
    'application': True,
    'auto_install': False,
}
