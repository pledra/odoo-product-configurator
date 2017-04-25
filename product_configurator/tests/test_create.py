# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ConfigurationCreate(TransactionCase):

    def test_create(self):
        """Test configuration item does not make variations"""

        attr_test = self.env['product.attribute'].create(
            {'name': 'Test',
             'value_ids': [
                 (0, 0, {'name': '1'}),
                 (0, 0, {'name': '2'}),
                 ],
             }
        )
        test_template = self.env['product.template'].create(
            {'name': 'Test Configuration',
             'config_ok': True,
             'type': 'product',
             'categ_id': self.env['ir.model.data'].xmlid_to_res_id(
                 'product.product_category_5'
             ),
             'attribute_line_ids': [
                 (0, 0, {'attribute_id': attr_test.id,
                         'value_ids': [
                             (6, 0, attr_test.value_ids.ids),
                             ],
                         'required': True,
                         }),
                 ]
             }
        )

        self.assertEqual(
            test_template.product_variant_count,
            0,
            "Create should not have any variants"
            )

