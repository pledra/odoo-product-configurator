{
    'name': 'Product Configuration Access Rights',
    'version': '11.0.1.1.0',
    'category': 'Generic Modules',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['product_configurator', 'auth_signup'],
    "data": [
        'security/configurator_security.xml',
        "data/menu_configurable_product.xml",
        'security/ir.model.access.csv',
    ],
    'images': [
        'static/description/cover.png'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
