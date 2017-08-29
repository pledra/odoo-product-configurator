# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Product Configurator Refactor",
    "summary": "To refactor product configurator",
    "version": "10.0.1.0.0",
    "license": "AGPL-3",
    "author": "Ursa Information Systems",
    "category": "Sales",
    "maintainer": "Ursa Information Systems",
    "website": "http://www.ursainfosystems.com",
    "depends": [
        "product_configurator_default_val"
    ],
    "qweb": [
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_attribute_value_line_view.xml",
        "views/product_attribute_views.xml",
        "views/product_view.xml",
    ],
    "application": False,
}
