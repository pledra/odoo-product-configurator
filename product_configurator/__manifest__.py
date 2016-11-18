# -*- coding: utf-8 -*-

{
    'name': 'Product Configurator Base',
    'version': '1.0',
    'category': 'Generic Modules/Base',
    'summary': 'Base for product configuration interface modules',
    'description': """
        Base module offering configurable template products as a
        set of instructions for configuration wizards/forms.

        Features offered include:

        - Inhibition of automatically created variants
        - Extension of attribute lines to offer required, custom and multiple
          selection
        - Configuration / Compatibility rules between attributes
        - Images for intermediate and final configurations
        - Set of helper methods required for any Odoo configuration module
    """,
    'author': 'Pledra',
    'license': 'AGPL-3',
    'website': 'http://www.pledra.com/',
    'depends': ['sale_stock'],
    "data": [
        'data/menu_configurable_product.xml',
        'data/product_attribute.xml',
        'security/configurator_security.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/sale_view.xml',
        'views/product_view.xml',
        'views/product_attribute_view.xml',
        'views/product_config_view.xml',
    ],
    'demo': [
        'demo/product_template.xml',
        'demo/product_attribute.xml',
        'demo/product_config_domain.xml',
        'demo/product_config_lines.xml',
        'demo/product_config_step.xml',
        'demo/config_image_ids.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}
