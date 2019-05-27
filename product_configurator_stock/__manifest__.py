{
    'name': 'Product Configurator for Stock',
    'version': '11.0.1.0.1',
    'category': 'Generic Modules/Stock',
    'summary': 'Product configuration interface module for Stock',
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['stock'],
    "data": [
        'views/stock_picking_view.xml',
        'views/stock_move_view.xml',
    ],
    'demo': [
        'demo/product_template.xml'
    ],
    'images': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
