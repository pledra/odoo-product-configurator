{
    'name': "Website Product Configurator",
    'version': '11.0.1.0.0',
    'summary': """Configure products in e-shop""",
    'author': "Pledra",
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'category': 'website',

    'depends': ['website_sale', 'product_configurator'],

    'data': [
        'data/config_form_templates.xml'
    ],
    'demo': [
    ],
    'images': [
        'static/description/cover.png'
    ],
    'application': True,
    'installable': True,
}
