{
    'name': 'Product Configurator Manufacturing',
    'version': '11.0.1.0.8',
    'category': 'Manufacturing',
    'summary': 'BOM Support for configurable products',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['mrp', 'product_configurator'],
    "data": [
        'views/mrp_view.xml',
        'views/product_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/product_template.xml'
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
