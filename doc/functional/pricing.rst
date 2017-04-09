.. _pricing-functional:

Pricing
-------

***********
Computation
***********

Computing prices for configurable products is done differently from the legacy method.

**Legacy method**

In order to compute prices for standard variants Odoo does the following:

1. Uses the product template price as a starting / base price.

2. Loops through all attribute values of the product variant

3. **Adds the template base price + sum of all price_extra fields on each attribute value.**


**Product configurator method**

Everything until step 2 remains the same. What is different is that we do not use the price_extra field
from the product.attribute.value.

Instead we use the price of the product linked to the product.attribute.value.

**Base price (product.template) + sum of all products related to the attribute.values on the variant.**

As such if you want to compute an extra price for a certain attribute, create a regular product, set a price and link the product to the attribute value in the form view.

.. note::

   In order for live pricing updates in the website configurator to work the same setup must be made

For a technical explanation on how this is implemented please check the :ref:`Pricing Technical <pricing-technical>`.

******
Format
******

The format in which the price is displayed depends on the user's language.

It follows the rules set in Settings->Languages-> * Language of the user *

If you want to apply another format that is not available in the language model visit :ref:`Pricing Technical <pricing-technical>`.
