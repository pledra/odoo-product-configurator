# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ProductVariant(TransactionCase):

    def setUp(self):
        super(ProductVariant, self).setUp()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().iteritems()
        }

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

    def test_product_create(self):
        """Test creation of a variant"""

        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]

        attr_val_ids = self.get_attr_val_ids(conf)
        product = self.cfg_tmpl.create_variant(attr_val_ids)
        self.assertTrue(
            set(attr_val_ids) == set(product.attribute_value_ids.ids),
            "Product not created with correct attributes")
        self.product = product

    def test_product_copy(self):
        """Test copy of a variant"""

        product2 = self.product.copy_configurable()
        self.assertTrue(
            set(self.product.attribute_value_ids.ids) ==
            set(product2.attribute_value_ids.ids),
            "Product configuration copy failed")
