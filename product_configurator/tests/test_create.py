from odoo.tests.common import TransactionCase


class ConfigurationCreate(TransactionCase):

    def setUp(self):
        super(ConfigurationCreate, self).setUp()

        self.ProductAttribute = self.env['product.attribute']
        self.ProductAttributeValue = self.env['product.attribute.value']
        self.ProductAttributeLine = self.env['product.attribute.line']
        self.ProductConfigDomain = self.env['product.config.domain']
        self.ProductConfigSteps = self.env['product.config.step']
        self.ProductConfWizard = self.env['product.configurator']
        self.attr_color = self.ProductAttribute.create({
            'name': 'Color',
        })
        self.attr_size = self.ProductAttribute.create({
            'name': 'Size',
        })
        self.attr_width = self.ProductAttribute.create({
            'name': 'Width',
        })
        self.value_blue = self.ProductAttributeValue.create({
            'name': 'Blue',
            'attribute_id': self.attr_color.id
        })
        self.value_green = self.ProductAttributeValue.create({
            'name': 'Green',
            'attribute_id': self.attr_color.id
        })
        self.value_S = self.ProductAttributeValue.create({
            'name': 'S',
            'attribute_id': self.attr_size.id
        })
        self.value_M = self.ProductAttributeValue.create({
            'name': 'M',
            'attribute_id': self.attr_size.id
        })
        self.value_L = self.ProductAttributeValue.create({
            'name': 'L',
            'attribute_id': self.attr_size.id
        })
        self.value_A = self.ProductAttributeValue.create({
            'name': 'A',
            'attribute_id': self.attr_width.id
        })
        self.value_B = self.ProductAttributeValue.create({
            'name': 'B',
            'attribute_id': self.attr_width.id
        })
        self.product_category = self.env.ref('product.product_category_5')
        self.step_1 = self.ProductConfigSteps.create({
            'name': 'Step: 1'
        })
        self.step_2 = self.ProductConfigSteps.create({
            'name': 'Step: 2'
        })

    def test_01_create(self):
        """Test configuration item does not make variations"""

        attr_test = self.env['product.attribute'].create({
            'name': 'Test',
            'value_ids': [
                (0, 0, {'name': '1'}),
                (0, 0, {'name': '2'}),
            ],
        })

        test_template = self.env['product.template'].create({
            'name': 'Test Configuration',
            'config_ok': True,
            'type': 'consu',
            'categ_id': self.product_category.id,
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attr_test.id,
                'value_ids': [
                    (6, 0, attr_test.value_ids.ids),
                ],
                'required': True,
            }),
            ]
        })

        self.assertEqual(test_template.product_variant_count, 0,
                         "Create should not have any variants")

    def test_02_product_configuration_restriction(self):
        """Values on future steps breaking current wizard view """

        restriction = self.ProductConfigDomain.create({
            'name': 'restriction-color',
            'domain_line_ids': [(0, 0, {
                'attribute_id': self.attr_color.id,
                'condition': 'in',
                'value_ids': [(6, 0, [self.value_blue.id])]
            })]
        })
        product = self.env['product.template'].create({
            'name': 'bug #59',
            'config_ok': True,
            'type': 'consu',
            'categ_id': self.product_category.id,
            'list_price': '20000',
        })
        attr_line1 = self.ProductAttributeLine.create({
            'attribute_id': self.attr_color.id,
            'value_ids': [(6, 0, [self.value_blue.id, self.value_green.id])],
            'required': True,
            'product_tmpl_id': product.id,
        })
        attr_line2 = self.ProductAttributeLine.create({
            'attribute_id': self.attr_size.id,
            'value_ids': [(6, 0, [self.value_S.id, self.value_M.id, self.value_L.id])],
            'required': True,
            'product_tmpl_id': product.id,
        })
        attr_line3 = self.ProductAttributeLine.create({
            'attribute_id': self.attr_width.id,
            'value_ids': [(6, 0, [self.value_A.id, self.value_B.id])],
            'required': True,
            'product_tmpl_id': product.id,
        })
        step1 = {
            'config_step_id': self.step_1.id,
            'attribute_line_ids': [(6, 0, [attr_line1.id])]
        }
        step2 = {
            'config_step_id': self.step_2.id,
            'attribute_line_ids': [(6, 0, [attr_line2.id, attr_line3.id])]
        }
        product.write({
            'config_step_line_ids': [(0, 0, step1), (0, 0, step2)],
            'config_line_ids': [(0, 0, {
                'attribute_line_id': attr_line2.id,
                'value_ids': [(6, 0, [self.value_M.id])],
                'domain_id': restriction.id
            })]
        })
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': product.id,
        })
        product_config_wizard.action_next_step()
        setattr(product_config_wizard, '__attribute-' + str(self.attr_color.id), str(self.value_blue.id))
        product_config_wizard.action_next_step()
        setattr(product_config_wizard, '__attribute-' + str(self.attr_size.id), str(self.value_M.id))
        product_config_wizard.action_previous_step()
        setattr(product_config_wizard, '__attribute-' + str(self.attr_color.id), str(self.value_green.id))
        product_config_wizard.action_next_step()
        setattr(product_config_wizard, '__attribute-' + str(self.attr_size.id), str(self.value_S.id))
        setattr(product_config_wizard, '__attribute-' + str(self.attr_width.id), str(self.value_A.id))
        product_config_wizard.action_next_step()
        new_variant = product.product_variant_ids.filtered(
            lambda variant: variant.attribute_value_ids == (self.value_green + self.value_S + self.value_A)
        )
        self.assertNotEqual(
            new_variant.id,
            False,
            'Error while configure product from ptoduct template form'
        )
