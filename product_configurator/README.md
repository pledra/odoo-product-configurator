#Odoo Product Configurator Base

This module has all the mechanics to support product configuration. It serves as a base dependency for configuration interfaces.

Features
========

- Inhibition of automatically created variants.
- Extension of attribute lines to offer required, custom and multiple selection.
- Configuration / Compatibility rules between attributes.
- Separation of attributes in different steps.
- Images for intermediate and final configurations.
- Managing active configuration sessions for external configurators
- Set of helper methods required for any Odoo configuration module.


Usage
=====

This module is only the foundation for external configuration interfaces such as 'product_configurator_wizard' or 'website_product_configurator'.

By itself this module does not configure custom products but offers the basis for generating, validating, updating configurable products using configuration interfaces.
