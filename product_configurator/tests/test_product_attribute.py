from odoo.tests.common import TransactionCase

class ProductAttributes(TransactionCase):

    def setUp(self):
        super(ProductAttributes, self).setUp()
        self.attributes = self.env.ref('product.product_attribute_1')

    def test_01_onchange_custome_type(self):
        self.attributes.min_val = 20
        self.attributes.max_val = 30
        self.attributes.custom_type = 'char'
        self.attributes.onchange_custom_type()
        self.assertEqual(
            self.attributes.min_val,
            0,
            'Min value is False'
        )
        self.assertEqual(
            self.attributes.max_val,
            0,
            "Max value is False"
        )

        self.attributes.min_val = 20
        self.attributes.max_val = 30
        self.attributes.custom_type = 'int'
        self.attributes.onchange_custom_type()
        self.assertEqual(
            self.attributes.min_val,
            20,
            "Min value is equal to existing min value"
        )
        self.assertEqual(
            self.attributes.max_val,
            30,
            "Max value is equal to existing max value"
        )

        self.attributes.custom_type = 'float'
        self.attributes.onchange_custom_type()
        self.assertEqual(
            self.attributes.min_val,
            20,
            "Min value is equal to existing min value when type is changed to integer to float"
        )
        self.assertEqual(
            self.attributes.max_val,
            30,
            "Max value is equal to existing max value when type is changed to integer to float"
        )

    def test_02_onchange_val_custom(self):
        self.attributes.val_custom = False
        self.attributes.custom_type = 'int'
        self.attributes.onchange_val_custom_field()
        self.assertFalse(
            self.attributes.custom_type,
            "custom_type is False"
        )