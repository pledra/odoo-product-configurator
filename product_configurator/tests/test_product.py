from odoo.addons.product_configurator.tests.\
    product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestProduct(ProductConfiguratorTestCases):

    def setUp(self):
        super(TestProduct, self).setUp()
        self.productTemplate = self.env['product.template']
        self.productAttributeLine = self.env['product.attribute.line']
        self.productConfigStepLine = self.env['product.config.step.line'] 
        self.product_category = self.env.ref('product.product_category_5')
        self.value_diesel = self.env.ref(
            'product_configurator.product_attribute_value_diesel')
        self.value_218d = self.env.ref(
            'product_configurator.product_attribute_value_218d')
        self.value_220d = self.env.ref(
            'product_configurator.product_attribute_value_220d')
        self.value_silver = self.env.ref(
            'product_configurator.product_attribute_value_silver')
        self.config_step_engine = self.env.ref(
            'product_configurator.config_step_engine')
        self.config_step_body = self.env.ref(
            'product_configurator.config_step_body')
        self.product_tmpl_id = self.env['product.template'].create({
            'name': 'Test Configuration',
            'config_ok': True,
            'type': 'consu',
            'categ_id': self.product_category.id,
        })
        # self.productId = self.env.ref(
        #     'product_configurator.product_bmw_sport_line')

    def test_00_template_vals(self):
        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_fuel.id,
            'value_ids': [(6, 0, [
                           self.value_gasoline.id,
                           self.value_diesel.id])],
            'required': True,
        })
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218i.id,
                           self.value_220i.id])],
            'required': True,
        })
        # create attribute line 2
        self.attributeLine3 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218d.id,
                           self.value_220d.id])],
            'required': True,
        })
        # create attribute line 1
        self.attributeLine4 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_color.id,
            'value_ids': [(6, 0, [
                           self.value_red.id,
                           self.value_silver.id])],
            'required': True,
        })
        self.product_tmpl_id.write({
            'attribute_line_ids': [(6, 0, [
                                    self.attributeLine1.id,
                                    self.attributeLine2.id,
                                    self.attributeLine3.id,
                                    self.attributeLine4.id])],
        })
        value_ids = self.product_tmpl_id.attribute_line_ids.mapped('value_ids')
        self.product_tmpl_id._compute_template_attr_vals()
        self.assertEqual(
            value_ids,
            self.product_tmpl_id.attribute_line_val_ids,
            'Error: if value are different\
            Method: _compute_template_attr_vals() '
        )

        # # create attribute value line 1
        # self.productConfigDomainLineId = self.env['product.config.domain.line'].create({
        #     'domain_id': self.productConfigDomainId.id,
        #     'attribute_id': self.attr_fuel.id,
        #     'condition': 'in',
        #     'value_ids': [(6, 0, [self.value_gasoline.id])],
        #     'operator': 'and',
        # })
        # self.productConfigLine = self.env['product.config.line'].create({
        #     'product_tmpl_id': self.product_tmpl_id.id,
        #     'attribute_line_id': self.attr_engine.id,
        #     'value_ids': [(6, 0, [
        #         self.value_218i.id,
        #         self.value_220i.id])],
        #     'domain_id': self.productConfigDomainLineId.id,
        # })
        # self.attribute_value_line_1 = self.productAttributeValueLine.create({
        #     'product_tmpl_id': self.product_tmpl_id.id,
        #     'value_id': self.attribute_vals_1.id,
        #     'value_ids': [(6, 0, [
        #                     self.attribute_vals_1.id,
        #                     self.attribute_vals_3.id])],
        # })
        # self.product_tmpl_id.write({
        #     'config_line_ids': [(0, 0, [])],
        # })
        self.product_tmpl_id.weight=120
        self.assertEqual(
            self.product_tmpl_id.weight,
            self.product_tmpl_id.weight_dummy,
            'Error: If set diffrent value for dummy_weight\
            Method: _set_weight()'
        )
        self.product_tmpl_id.weight_dummy = 50.0
        self.product_tmpl_id._compute_weight()
        self.assertEqual(
            self.product_tmpl_id.weight_dummy,
            self.product_tmpl_id.weight,
            'Error: If set diffrent value for weight\
            Method: _compute_weight()'
        )
        attribute_value_action = self.product_tmpl_id.get_product_attribute_values_action()
        contextValue = attribute_value_action.get('context')
        self.assertEqual(
            contextValue['active_id'],
            self.product_tmpl_id.id,
            'Error: If different template id\
            Method: get_product_attribute_values_action()'
        )
        configFalse = self.product_tmpl_id.toggle_config()
        self.assertFalse(
            configFalse,
            'Error: If Boolean False\
            Method: toggle_config()'
        )
        self.product_tmpl_id.toggle_config()
        varient_value = self.product_tmpl_id.create_variant_ids()
        self.assertIsNone(
            varient_value,
            'Error: If its return none\
            Method: create_variant_ids()'
        )
        # self.product_tmpl_id.config = True
        #  varient_value2 = self.product_tmpl_id.toggle_config()
        # self.assertTrue(
        #     varient_value2,
        #     'Error: If its return True\
        #     Method: create_variant_ids()'
        # )
        # self.product_tmpl_id.toggle_config()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218d.id,
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        product_config_wizard.action_next_step()
        config_session_id = self.env['product.config.session'].search([(
            'product_tmpl_id', '=', self.product_tmpl_id.id)])
        config_session_id.unlink()
        varientId = self.product_tmpl_id.product_variant_ids
        boolValue = varientId.unlink()
        self.assertTrue(
            boolValue,
            'Error: if record are not unlink\
            Method: unlink()'
        )

    def test_01_configure_product(self):
        # configure product
        self.product_tmpl_id.configure_product()
        self.ProductConfWizard.action_next_step()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        with self.assertRaises(ValidationError):
            product_config_wizard.action_next_step()

        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_fuel.id,
            'value_ids': [(6, 0, [
                           self.value_gasoline.id,
                           self.value_diesel.id])],
            'required': True,
        })
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218i.id,
                           self.value_220i.id,
                           self.value_218d.id,
                           self.value_220d.id])],
            'required': True,
        })
        # create attribute line 3
        self.attributeLine3 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attr_color.id,
            'value_ids': [(6, 0, [
                           self.value_red.id,
                           self.value_silver.id])],
            'required': True,
        })
        self.product_tmpl_id.write({
            'attribute_line_ids': [(6, 0, [
                                    self.attributeLine1.id,
                                    self.attributeLine2.id,
                                    self.attributeLine3.id])],
        })
        product_config_wizard.action_next_step()
        self.assertEqual(
            product_config_wizard.state,
            'configure',
            'Error: If state are different\
            Method: action_next_step()'
        )
        with self.assertRaises(UserError):
            product_config_wizard.action_next_step()

        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        wizard_action = product_config_wizard.action_next_step()
        varient_id = wizard_action.get('res_id')
        self.assertEqual(
            varient_id,
            self.product_tmpl_id.product_variant_ids.id,
            'Error: If get diffrent varient Id\
            Method: action_next_step()'
        )
        product_config_wizard.action_previous_step()
        self.assertEqual(
            product_config_wizard.state,
            'select',
            'Error: If get diffrent State\
            Method: action_previous_step()'
        )
        # create config_step_line 1
        self.configStepLine1 = self.productConfigStepLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'config_step_id': self.config_step_engine.id,
            'attribute_line_ids': [(6, 0, [
                self.attributeLine1.id,
                self.attributeLine2.id])]
        })
        # create config_step_line 2
        self.configStepLine2 = self.productConfigStepLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'config_step_id': self.config_step_body.id,
            'attribute_line_ids': [(6, 0, [
                self.attributeLine3.id])]
        })
        self.product_tmpl_id.write({
            'config_step_line_ids': [(6, 0, [
                                    self.configStepLine1.id,
                                    self.configStepLine2.id])],
        })
        # configure product
        self.product_tmpl_id.configure_product()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        product_config_wizard.action_previous_step()
        self.assertEqual(
            product_config_wizard.state,
            str(self.configStepLine1.id),
            'Error: If diffrent previous state and config state\
            Method: action_previous_step()'
        )
        product_config_wizard.action_next_step()
        self.assertEqual(
            product_config_wizard.config_session_id.config_step,
            product_config_wizard.state,
            'Error: If diffrent state and config_step\
            Method: action_previous_step()'
        )
        product_config_wizard.action_next_step()

        # check for product_product
        product_product = self.product_tmpl_id.product_variant_ids
        mako_tmpl_vals = product_product._get_mako_tmpl_name()
        self.assertEqual(
            mako_tmpl_vals,
            product_product.display_name,
            'Error: If get display_name are different\
            Method: _get_mako_tmpl_name()'
        )
        self.product_tmpl_id.write({
            'mako_tmpl_name': 'Test Configuration Product'
        })
        mako_tmpl_vals = product_product._get_mako_tmpl_name()
        self.assertEqual(
            self.product_tmpl_id.mako_tmpl_name,
            mako_tmpl_vals,
            'Error: If Mako Template are not exists or different\
            Method: _get_mako_tmpl_name()'
        )
        self.product_tmpl_id.weight = 10
        product_product.weight_extra = 20
        product_product._compute_product_weight()
        self.assertEqual(
            product_product.weight,
            30,
            'Error: If value are not get 30\
            Method: _compute_product_weight()'
        )
        product_product.config_ok = False
        product_product.weight_dummy = 50
        product_product._compute_product_weight()
        self.assertEqual(
            product_product.weight,
            50,
            'Error: If value are not get 50\
            Method: _compute_product_weight()'
        )
        varient_price = product_product.get_product_attribute_values_action()
        context_vals = varient_price['context']
        self.assertEqual(
            context_vals['default_product_tmpl_id'],
            product_product.product_tmpl_id.id,
            'Error: If different template id\
            Method: get_product_attribute_values_action()'
        )
        # product_product.unlink()
        product_product._compute_name()
        self.assertEqual(
            product_product.config_name,
            'Test Configuration',
            'Error: If different product config_name\
            Method: _compute_name()'
        )
        product_product.config_ok = True
        self.assertEqual(
            product_product.config_name,
            'Test Configuration',
            'Error: If different product config_name\
            Method: _compute_name()'
        )
        
        # reconfigure product
        product_product.reconfigure_product()
        
        # configure product
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218d.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_silver.id,
        })
        product_config_wizard.action_next_step()
        value_ids = self.value_gasoline + self.value_218d + self.value_silver
        new_variant = self.product_tmpl_id.product_variant_ids.filtered(
            lambda variant:
            variant.attribute_value_ids == value_ids
        )
        self.assertTrue(
            new_variant.id,
            'Error: if varient id not exists\
            Method: reconfigure_product()'
        )

        # _compute_product_weight_extra
        productAttPrice = self.env['product.attribute.price'].create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'value_id': self.value_gasoline.id,
            'weight_extra': 45
        })
        self.assertEqual(
            productAttPrice.weight_extra,
            new_variant.weight_extra,
            'weight_extra not equal'
        )