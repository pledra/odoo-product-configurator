from odoo.tests.common import TransactionCase

class ProductAttributes(TransactionCase):

    def setUp(self):
        super(ProductAttributes, self).setUp()
        self.attribute_1 = self.env.ref('product.product_attribute_1')

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