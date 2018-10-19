{
    'name': 'Product Configurator Purchase',
    'version': '11.0.1.0.1',
    'category': 'Generic Modules/Purchase',
    'summary': 'Product configuration interface for Purchase',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['purchase', 'product_configurator'],
    "data": [
        'data/menu_product.xml',
        'views/purchase_view.xml',
    ],
    'demo': [
        'demo/product_template.xml',
    ],
    'images': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
