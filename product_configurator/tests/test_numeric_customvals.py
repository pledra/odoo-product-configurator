# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class ConfigurationRules(TransactionCase):

    def setUp(self):
        super(ConfigurationRules, self).setUp()

        self.attr_repeater = self.env['product.attribute'].create(
            {'name': 'Repeater',
             'value_ids': [
                 (0, 0, {'name': '1'}),
                 (0, 0, {'name': '2'}),
                 ],
             'custom_type': 'int',
             'min_val': 3,
             'max_val': 10,
             }
        )
        self.attr_flux = self.env['product.attribute'].create(
            {'name': 'Flux Adjustment',
             'value_ids': [
                 (0, 0, {'name': 'Standard'}),
                 ],
             'custom_type': 'float',
             'custom_digits': 3,
             'min_fval': 0.750,
             'max_fval': 1.823,
             }
        )
        self.flux_capacitor = self.env['product.template'].create(
            {'name': 'Flux Capacitor',
             'config_ok': True,
             'type': 'product',
             'categ_id': self.env['ir.model.data']  .xmlid_to_res_id(
                 'product.product_category_5'
             ),
             'attribute_line_ids': [
                 (0, 0, {'attribute_id': self.attr_repeater.id,
                         'value_ids': [
                             (6, 0, self.attr_repeater.value_ids.ids),
                             ],
                         'required': True,
                         'custom': True,
                         }),
                 (0, 0, {'attribute_id': self.attr_flux.id,
                         'value_ids': [
                             (6, 0, self.attr_flux.value_ids.ids),
                             ],
                         'required': True,
                         'custom': True,
                         })
                 ]
             }
        )

    def test_without_custom(self):
        attr_val_ids = [self.attr_repeater.value_ids[0].id,
                        self.attr_flux.value_ids[0].id,
                        ]
        custom_vals = {}
        validation = self.flux_capacitor.validate_configuration(
            attr_val_ids, custom_vals)
        self.assertTrue(
            validation,
            "Configuration with custom values rejected with all "
            "standard selections"
        )

    def test_valid_custom_numerics(self):
        attr_val_ids = []
        custom_vals = {
            self.attr_repeater.id: '5',
            self.attr_flux.id: '1.234',
        }
        validation = self.flux_capacitor.validate_configuration(
            attr_val_ids, custom_vals)
        self.assertTrue(
            validation,
            "Configuration with valid custom numeric values rejected"
        )

    def test_invalid_custom_numerics(self):
        attr_val_ids = []
        validation_method = self.flux_capacitor.validate_configuration

        custom_vals = {
            self.attr_repeater.id: '2',
            self.attr_flux.id: '1.234',
        }
        self.assertRaises(ValidationError,
                          validation_method, attr_val_ids, custom_vals)

        custom_vals = {
            self.attr_repeater.id: '11',
            self.attr_flux.id: '1.234',
        }
        self.assertRaises(ValidationError,
                          validation_method, attr_val_ids, custom_vals)

        custom_vals = {
            self.attr_repeater.id: '5',
            self.attr_flux.id: '0.749',
        }
        self.assertRaises(ValidationError,
                          validation_method, attr_val_ids, custom_vals)

        custom_vals = {
            self.attr_repeater.id: '5',
            self.attr_flux.id: '1.824',
        }
        self.assertRaises(ValidationError,
                          validation_method, attr_val_ids, custom_vals)
