{
    'name': 'Product Configurator Manufacturing',
    'version': '11.0.1.0.2',
    'category': 'Manufacturing',
    'summary': 'BOM Support for configurable products',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['mrp', 'product_configurator'],
    "data": [
        'security/configurator_security.xml',
        'security/ir.model.access.csv',
        'views/mrp_view.xml',
    ],
    'demo': [
        'demo/product_template.xml'
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
