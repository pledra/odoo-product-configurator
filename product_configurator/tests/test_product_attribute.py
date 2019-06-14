from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class ProductAttributes(TransactionCase):

    def setUp(self):
        super(ProductAttributes, self).setUp()
        self.ProductAttributeFuel = self.env.ref(
            'product_configurator.product_attribute_fuel')
        self.ProductAttributeLineFuel = self.env.ref(
            'product_configurator.product_attribute_line_2_series_fuel')
        self.ProductAttributeValueGasoline = self.env.ref(
            'product_configurator.product_attribute_value_gasoline')
        self.ProductAttributeValueFuel = \
            self.ProductAttributeValueGasoline.attribute_id.id
        self.ProductTemplate = self.env.ref(
            'product_configurator.bmw_2_series')
        self.ProductAttributePrice = self.env['product.attribute.price']

    def test_01_onchange_custome_type(self):
        self.ProductAttributeFuel.min_val = 20
        self.ProductAttributeFuel.max_val = 30
        self.ProductAttributeFuel.custom_type = 'char'
        self.ProductAttributeFuel.onchange_custom_type()
        self.assertEqual(
            self.ProductAttributeFuel.min_val,
            0,
            'Min value is not False'
        )
        self.assertEqual(
            self.ProductAttributeFuel.max_val,
            0,
            "Max value is not False"
        )

        self.ProductAttributeFuel.min_val = 20
        self.ProductAttributeFuel.max_val = 30
        self.ProductAttributeFuel.custom_type = 'int'
        self.ProductAttributeFuel.onchange_custom_type()
        self.assertEqual(
            self.ProductAttributeFuel.min_val,
            20,
            "Min value is not equal to existing min value"
        )
        self.assertEqual(
            self.ProductAttributeFuel.max_val,
            30,
            "Max value is not equal to existing max value"
        )

        self.ProductAttributeFuel.custom_type = 'float'
        self.ProductAttributeFuel.onchange_custom_type()
        self.assertEqual(
            self.ProductAttributeFuel.min_val,
            20,
            "Min value is equal to existing min value \
            when type is changed to integer to float"
        )
        self.assertEqual(
            self.ProductAttributeFuel.max_val,
            30,
            "Max value is equal to existing max value \
            when type is changed to integer to float"
        )

    def test_02_onchange_val_custom(self):
        self.ProductAttributeFuel.val_custom = False
        self.ProductAttributeFuel.custom_type = 'int'
        self.ProductAttributeFuel.onchange_val_custom_field()
        self.assertFalse(
            self.ProductAttributeFuel.custom_type,
            "custom_type is not False"
        )

    def test_03_check_searchable_field(self):
        self.ProductAttributeFuel.custom_type = 'binary'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.search_ok = True

    def test_04_validate_custom_val(self):
        self.ProductAttributeFuel.write({
            'max_val': 20,
            'min_val': 10
        })
        self.ProductAttributeFuel.custom_type = 'int'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.validate_custom_val(5)

        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.validate_custom_val(30)

    def test_05_check_constraint_min_max_value(self):
        self.ProductAttributeFuel.custom_type = 'int'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.min_val = 110

    def test_06_onchange_attribute(self):
        self.ProductAttributeLineFuel.onchange_attribute()
        self.assertFalse(
            self.ProductAttributeLineFuel.value_ids,
            "value_ids is not False"
        )
        self.assertTrue(
            self.ProductAttributeLineFuel.required,
            "required not exsits value"
        )
        self.ProductAttributeLineFuel.multi = True
        self.assertTrue(
            self.ProductAttributeLineFuel.multi,
            "multi not exsits value"
        )
        self.ProductAttributeLineFuel.custom = True
        self.assertTrue(
            self.ProductAttributeLineFuel.custom,
            "custom not exsits value"
        )

    def test_07_check_default_values(self):
        with self.assertRaises(ValidationError):
            self.ProductAttributeLineFuel.default_val = \
                self.ProductAttributeValueFuel

    def test_08_compute_weight_extra(self):
        self.assertEqual(
            self.ProductAttributeValueGasoline.weight_extra,
            0.0,
            "weight_extra not 0.0"
        )
        self.ProductAttributeValueGasoline = \
            self.ProductAttributeValueGasoline.with_context(
                active_id=self.ProductTemplate.id)
        self.ProductAttributeValueGasoline.weight_extra = 14
        self.ProductAttributeValueGasoline._compute_weight_extra()
        self.assertEqual(
            self.ProductAttributeValueGasoline.price_ids.weight_extra,
            14,
            "weight_extra not exsits"
        )
        self.ProductAttributeValueGasoline.price_ids.weight_extra = 15
        self.ProductAttributeValueGasoline._compute_weight_extra()
        self.assertEqual(
            self.ProductAttributeValueGasoline.weight_extra,
            15,
            "values are not equal"
        )

    # TODO :: Left to create method
    def test_09_inverse_weight_extra(self):
        self.ProductAttributePrice = self.ProductAttributePrice.create({
            'product_tmpl_id': self.ProductTemplate.id,
            'value_id': 10,
            'weight_extra': 12,
        })
        self.ProductAttributeValueGasoline = \
            self.ProductAttributeValueGasoline.with_context(
                active_id=self.ProductTemplate.id)
        self.ProductAttributeValueGasoline.weight_extra = 14
        self.ProductAttributeValueGasoline._compute_weight_extra()
        self.assertEqual(
            14,
            self.ProductAttributeValueGasoline.weight_extra,
            "weight_extra not exsits"
        )
        self.assertEqual(
            self.ProductAttributeValueGasoline.price_ids.weight_extra,
            14,
            "weight_extra not exsits"
        )
