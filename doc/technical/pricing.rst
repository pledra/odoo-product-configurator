.. _pricing-technical:

=======
Pricing
=======

Computation
-----------

As explained in the :ref:`Functional Section <pricing-functional>`, the final price of the variant
is a sum of the product.template price + all related products of the selected attribute.values.

We managed to do this by using the 'config_ok' boolean field to differentiate between regular products and configurable ones.

By inheriting the `_compute_product_price_extra <https://github.com/odoo/odoo/blob/10.0/addons/product/models/product.py#L211>`_ method we delegate regular products to the original method and new ones to `ours <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L437>`_

Format
-----------

Whenever the price of a configuration needs to be computed (regardless of the configuration interface used), the `get_cfg_price <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L122>`_ method is called. The keyword argument formatLang determines if the output is formatted by the settings on the user's language or regular float type for computation.

If formatLang keyword argument is True then before returning the computed values the `formatPrices <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L112>`_ method is called.

`formatPrices <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L112>`_ takes the output of `get_cfg_price <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L122>`_ method and applied Odoo's formatLang method on the result.

If the language settings applied via formatLang do not satisfy your needs, you need to inherit the `formatPrices <https://github.com/pledra/odoo-product-configurator/blob/10.0/product_configurator/models/product.py#L112>`_ method and apply your own formatting rules.







