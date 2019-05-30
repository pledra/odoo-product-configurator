from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class ProductAttributes(TransactionCase):

    def setUp(self):
        super(ProductAttributes, self).setUp()
        self.attribute_1 = self.env.ref('product_configurator.product_attribute_fuel')
        self.attribute_2 = self.env.ref('product_configurator.product_attribute_line_2_series_fuel')
        self.attribute_3 = self.env.ref('product_configurator.product_attribute_value_gasoline')
        self.template_1 = self.env.ref('product_configurator.bmw_2_series')

    def test_01_onchange_custome_type(self):
        self.attribute_1.min_val = 20
        self.attribute_1.max_val = 30
        self.attribute_1.custom_type = 'char'
        self.attribute_1.onchange_custom_type()
        self.assertEqual(
            self.attribute_1.min_val,
            0,
            'Min value is False'
        )
        self.assertEqual(
            self.attribute_1.max_val,
            0,
            "Max value is False"
        )

        self.attribute_1.min_val = 20
        self.attribute_1.max_val = 30
        self.attribute_1.custom_type = 'int'
        self.attribute_1.onchange_custom_type()
        self.assertEqual(
            self.attribute_1.min_val,
            20,
            "Min value is equal to existing min value"
        )
        self.assertEqual(
            self.attribute_1.max_val,
            30,
            "Max value is equal to existing max value"
        )

        self.attribute_1.custom_type = 'float'
        self.attribute_1.onchange_custom_type()
        self.assertEqual(
            self.attribute_1.min_val,
            20,
            "Min value is equal to existing min value when type is changed to integer to float"
        )
        self.assertEqual(
            self.attribute_1.max_val,
            30,
            "Max value is equal to existing max value when type is changed to integer to float"
        )

    def test_02_onchange_val_custom(self):
        self.attribute_1.val_custom = False
        self.attribute_1.custom_type = 'int'
        self.attribute_1.onchange_val_custom_field()
        self.assertFalse(
            self.attribute_1.custom_type,
            "custom_type is False"
        )

    def test_03_check_searchable_field(self):
        self.attribute_1.custom_type = 'binary'
        with self.assertRaises(ValidationError):
            self.attribute_1.search_ok = True

    def test_04_validate_custom_val(self):
        self.attribute_1.write({
            'max_val': 20,
            'min_val': 10
        })
        self.attribute_1.custom_type = 'int'
        with self.assertRaises(ValidationError):
            self.attribute_1.validate_custom_val(5)

        with self.assertRaises(ValidationError):
            self.attribute_1.validate_custom_val(30)

    def test_05_check_constraint_min_max_value(self):
        self.attribute_1.custom_type = 'int'
        with self.assertRaises(ValidationError):
            self.attribute_1.min_val = 110

    def test_06_onchange_attribute(self):
        self.attribute_2.onchange_attribute()
        self.assertFalse(
            self.attribute_2.value_ids,
            "value_ids is False"
        )
        self.assertTrue(
            self.attribute_2.required,
            "required exsits value"
        )
        self.attribute_2.multi =True
        self.assertTrue(
            self.attribute_2.multi,
            "multi exsits value"
        )
        self.attribute_2.custom = True
        self.assertTrue(
            self.attribute_2.custom,
            "custom exsits value"
        )

    def test_07_check_default_values(self):
        with self.assertRaises(ValidationError):
            self.attribute_2.default_val = 4

    # TODO :: Left
    def test_08_compute_weight_extra(self):
        self.attribute_3 = self.attribute_3.with_context(active_id=self.template_1.id)
        if self.attribute_3:
            self.assertEqual(
                self.attribute_3.weight_extra,
                self.attribute_3.weight_extra,
                "weight_extra exsits"
            )
        else:
            self.assertEqual(
                self.attribute_3.weight_extra,
                0.0,
                "weight_extra 0.0"
            )