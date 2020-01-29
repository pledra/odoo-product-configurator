from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class ProductAttributes(TransactionCase):

    def setUp(self):
        super(ProductAttributes, self).setUp()
        self.productAttributeLine = self.env['product.template.attribute.line']
        self.ProductAttributeFuel = self.env.ref(
            'product_configurator.product_attribute_fuel')
        self.ProductAttributeLineFuel = self.env.ref(
            'product_configurator.product_attribute_line_2_series_fuel')
        self.ProductTemplate = self.env.ref(
            'product_configurator.bmw_2_series')
        self.product_category = self.env.ref('product.product_category_5')
        self.ProductAttributePrice = \
            self.env['product.template.attribute.value']
        self.attr_fuel = self.env.ref(
            'product_configurator.product_attribute_fuel')
        self.attr_engine = self.env.ref(
            'product_configurator.product_attribute_engine')
        self.value_diesel = self.env.ref(
            'product_configurator.product_attribute_value_diesel')
        self.value_218i = self.env.ref(
            'product_configurator.product_attribute_value_218i')
        self.value_gasoline = self.env.ref(
            'product_configurator.product_attribute_value_gasoline')
        self.ProductAttributeValueFuel = \
            self.value_gasoline.attribute_id.id

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
        self.ProductAttributeFuel.custom_type = 'integer'
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
        self.ProductAttributeFuel.custom_type = 'binary'
        self.ProductAttributeFuel.onchange_custom_type()
        self.assertFalse(
            self.ProductAttributeFuel.search_ok,
            'Error: if search true\
            Method: onchange_custom_type()'
        )

    def test_02_onchange_val_custom(self):
        self.ProductAttributeFuel.val_custom = False
        self.ProductAttributeFuel.custom_type = 'integer'
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
        self.ProductAttributeFuel.custom_type = 'integer'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.validate_custom_val(5)

        self.ProductAttributeFuel.write({
            'max_val': 0,
            'min_val': 10
        })
        self.ProductAttributeFuel.custom_type = 'integer'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.validate_custom_val(5)

        self.ProductAttributeFuel.write({
            'min_val': 0,
            'max_val': 20
        })
        self.ProductAttributeFuel.custom_type = 'integer'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.validate_custom_val(25)

    def test_05_check_constraint_min_max_value(self):
        self.ProductAttributeFuel.custom_type = 'integer'
        with self.assertRaises(ValidationError):
            self.ProductAttributeFuel.write({
                'max_val': 10,
                'min_val': 20
            })

    def test_06_onchange_attribute(self):
        with self.env.do_in_onchange():
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
                self.value_218i.id

    def test_08_copy_attribute(self):
        copyAttribute = self.ProductAttributeFuel.copy()
        self.assertEqual(
            copyAttribute.name,
            'Fuel (copy)',
            'Error: If not copy attribute\
            Method: copy()'
        )

    def test_09_compute_get_value_id(self):
        attrvalline = self.env[
            'product.attribute.value.line'].create({
                'product_tmpl_id': self.ProductTemplate.id,
                'value_id': self.value_gasoline.id
            })
        self.assertTrue(
            attrvalline.product_value_ids,
            'Error: If product_value_ids not exists\
            Method: _compute_get_value_id()'
        )

    def test_10_validate_configuration(self):
        with self.assertRaises(ValidationError):
            self.env['product.attribute.value.line'].create({
                'product_tmpl_id': self.ProductTemplate.id,
                'value_id': self.value_diesel.id,
                'value_ids': [(6, 0, [
                    self.value_218i.id]
                )]
            })

    def test_11_copy(self):
        default = {}
        productattribute = self.value_gasoline.copy(default)
        self.assertEqual(
            productattribute.name,
            self.value_gasoline.name + " (copy)",
            'Error: If not equal productattribute name\
            Method: copy()'
        )

    def test_12_onchange_values(self):
        productattributeline = self.env['product.template.attribute.line']
        productattributeline.onchange_values()
        self.assertEqual(
            productattributeline.default_val,
            productattributeline.value_ids,
            'Error: If default_val not exists\
            Method: onchange_values()'
            )
