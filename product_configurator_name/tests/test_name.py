# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ConfigurationCreate(TransactionCase):

    def setUp(self):
        super(ConfigurationCreate, self).setUp()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().iteritems()
        }

        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]

        self.attr_val_ids = self.get_attr_val_ids(conf)

    def get_attr_val_ids(self, ext_ids):
        """Return a list of database ids using the external_ids
        passed via ext_ids argument"""

        value_ids = []

        attr_val_prefix = 'product_configurator.product_attribute_value_%s'

        for ext_id in ext_ids:
            if ext_id in self.attr_val_ext_ids:
                value_ids.append(self.attr_val_ext_ids[ext_id])
            elif attr_val_prefix % ext_id in self.attr_val_ext_ids:
                value_ids.append(
                    self.attr_val_ext_ids[attr_val_prefix % ext_id]
                )

        return value_ids

    def test_name_get_odoo(self):
        """Test variant with name_override set"""

        variant = self.env.ref('product.product_product_11')

        res = variant.name_get()
        expected = [(variant.id, '[E-COM12] iPod (16 GB)')]
        self.assertEqual(res, expected, 'Product should display iPod name')

    def test_name_get_name_override(self):
        """Test variant with name_override set"""

        variant = self.cfg_tmpl.create_get_variant(self.attr_val_ids)
        variant.name_override = 'override'

        res = variant.name_get()
        expected = [(variant.id, 'override')]
        self.assertEqual(res, expected, 'Product should display name_override')

    def test_name_get_default(self):
        """Test variant as is"""

        variant = self.cfg_tmpl.create_get_variant(self.attr_val_ids)

        res = variant.name_get()
        expected = [(variant.id,
            '2 Series (Gasoline, 228i, Model Luxury Line, Silver, Double-spoke 18", '
            'Black, Automatic (Steptronic), Smoker Package, Tow hook)')]
        self.assertEqual(res, expected, 'Product name should display all values by default')

    def test_name_get_hide(self):
        """Test variant name with hidden lines"""
        color_line = self.env.ref('product_configurator.product_attribute_line_2_series_color')
        color_line.display_mode = 'hide'

        variant = self.cfg_tmpl.create_get_variant(self.attr_val_ids)

        res = variant.name_get()
        expected = [(variant.id,
            '2 Series (Gasoline, 228i, Model Luxury Line, Double-spoke 18", '
            'Black, Automatic (Steptronic), Smoker Package, Tow hook)')]
        self.assertEqual(res, expected, 'Product name should hide color attribute')

    def test_name_get_with_label(self):
        """Test variant name with hidden lines"""
        color_line = self.env.ref('product_configurator.product_attribute_line_2_series_color')
        color_line.display_mode = 'attribute'

        variant = self.cfg_tmpl.create_get_variant(self.attr_val_ids)

        res = variant.name_get()
        expected = [(variant.id,
            '2 Series (Gasoline, 228i, Model Luxury Line, Color: Silver, Double-spoke 18", '
            'Black, Automatic (Steptronic), Smoker Package, Tow hook)')]
        self.assertEqual(res, expected, 'Product name should display color attribute label')
