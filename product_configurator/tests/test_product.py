from ..tests.test_product_configurator_test_cases import \
    ProductConfiguratorTestCases
from odoo.exceptions import ValidationError


class TestProduct(ProductConfiguratorTestCases):

    def setUp(self):
        super(TestProduct, self).setUp()
        self.productTemplate = self.env['product.template']
        self.productAttributeLine = self.env['product.template.attribute.line']
        self.productConfigStepLine = self.env['product.config.step.line']
        self.product_category = self.env.ref('product.product_category_5')
        self.attributelinefuel = self.env.ref(
            'product_configurator.product_attribute_line_2_series_fuel')
        self.attributelineengine = self.env.ref(
            'product_configurator.product_attribute_line_2_series_engine')
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

    def _get_product_id(self):
        self._configure_product_nxt_step()
        return self.config_product.product_variant_ids

    def test_00__compute_template_attr_vals(self):
        value_ids = self.product_tmpl_id.attribute_line_ids.mapped('value_ids')
        self.product_tmpl_id._compute_template_attr_vals()
        self.assertEqual(
            value_ids,
            self.product_tmpl_id.attribute_line_val_ids,
            'Error: if value are different\
            Method: _compute_template_attr_vals() '
        )

    def test_01_set_weight(self):
        self.product_tmpl_id.weight = 120
        self.product_tmpl_id._set_weight()
        self.assertEqual(
            self.product_tmpl_id.weight,
            self.product_tmpl_id.weight_dummy,
            'Error: If set diffrent value for dummy_weight\
            Method: _set_weight()'
        )
        self.product_tmpl_id.config_ok = False
        set_weight = self.product_tmpl_id._set_weight()
        self.assertIsNone(
            set_weight,
            'Error: If Value none\
            Method: _set_weight()'
        )

    def test_02_compute_weight(self):
        self.product_tmpl_id.weight_dummy = 50.0
        self.product_tmpl_id._compute_weight()
        self.assertEqual(
            self.product_tmpl_id.weight_dummy,
            self.product_tmpl_id.weight,
            'Error: If set diffrent value for weight\
            Method: _compute_weight()'
        )

    def test_03_get_product_attribute_values_action(self):
        attribute_value_action = self.product_tmpl_id.\
            get_product_attribute_values_action()
        contextValue = attribute_value_action.get('context')
        self.assertEqual(
            contextValue['active_id'],
            self.product_tmpl_id.id,
            'Error: If different template id\
            Method: get_product_attribute_values_action()'
        )

    def test_04_toggle_config(self):
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

    def test_05_unlink(self):
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

    def test_06_check_default_values(self):
        self.attributelinefuel.default_val = self.value_gasoline.id,
        self.attributelineengine.default_val = self.value_218d.id
        with self.assertRaises(ValidationError):
            self.config_product._check_default_values()

    def test_07_configure_product(self):
        # configure product
        self.product_tmpl_id.configure_product()
        self.ProductConfWizard.action_next_step()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
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
                self.configStepLine2.id]
            )],
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

    def test_08_get_mako_tmpl_name(self):
        # check for product_product
        product_product = self._get_product_id()
        mako_tmpl_vals = product_product._get_mako_tmpl_name()
        self.assertEqual(
            mako_tmpl_vals,
            product_product.display_name,
            'Error: If get display_name are different\
            Method: _get_mako_tmpl_name()'
        )
        self.config_product.write({
            'mako_tmpl_name': 'Test Configuration Product'
        })
        mako_tmpl_vals = product_product._get_mako_tmpl_name()
        self.assertEqual(
            self.config_product.mako_tmpl_name,
            mako_tmpl_vals,
            'Error: If Mako Template are not exists or different\
            Method: _get_mako_tmpl_name()'
        )

    def test_09_compute_product_weight(self):
        product_product = self._get_product_id()
        self.config_product.weight = 10
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

    def test_10_get_product_attribute_values_action(self):
        product_product = self._get_product_id()
        varient_price = product_product.get_product_attribute_values_action()
        context_vals = varient_price['context']
        self.assertEqual(
            context_vals['default_product_tmpl_id'],
            product_product.product_tmpl_id.id,
            'Error: If different template id\
            Method: get_product_attribute_values_action()'
        )

    def test_11_compute_config_name(self):
        product_product = self._get_product_id()
        product_product.config_ok = False
        product_product._compute_config_name()
        self.assertEqual(
            product_product.config_name,
            '2 Series',
            'Error: If different product config_name\
            Method: _compute_config_name()'
        )
        product_product.config_ok = True
        product_product._compute_config_name()
        self.assertEqual(
            product_product.config_name,
            '2 Series',
            'Error: If different product config_name\
            Method: _compute_config_name()'
        )

    def test_12_reconfigure_product(self):
        self.product_tmpl_id.configure_product()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        product_config_wizard.action_next_step()
        # reconfigure product
        product_product = self.product_tmpl_id.product_variant_ids
        product_product.reconfigure_product()
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
            variant.attribute_value_ids
            == value_ids
        )
        self.assertTrue(
            new_variant.id,
            'Error: if varient id not exists\
            Method: reconfigure_product()'
        )

    def test_13_compute_product_weight_extra(self):
        product_product = self._get_product_id()
        # _compute_product_weight_extra
        productAttPrice = self.env['product.template.attribute.value'].create({
            'product_tmpl_id': self.config_product.id,
            'product_attribute_value_id': self.value_gasoline.id,
            'weight_extra': 45
        })
        self.assertEqual(
            productAttPrice.weight_extra,
            product_product.weight_extra,
            'Error: If weight_extra not equal\
            Method: _compute_product_weight_extra()'
        )

    def test_14_unlink(self):
        product_product = self._get_product_id()
        unlinkVals = product_product.unlink()
        self.assertTrue(
            unlinkVals,
            'Error: If unlink record true\
            Method: unlink()'
        )

    def test_15_copy(self):
        vals = self.config_product.copy()
        self.assertEqual(
            vals.name,
            '2 Series (copy)',
            'Error: If not equal\
            Method: copy()'
        )
        self.assertTrue(
            vals.attribute_line_ids,
            'Error: If attribute_line_ids not exists\
            Method: copy()'
        )

    def test_16_validate_unique_config(self):
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_gasoline.id,
                'value_ids': [(6, 0, [
                    self.value_218i.id
                ])]
            })]
        })
        with self.assertRaises(ValidationError):
            self.product_tmpl_id.write({
                'attribute_value_line_ids': [(0, 0, {
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'value_id': self.value_gasoline.id,
                    'value_ids': [(6, 0, [
                        self.value_218i.id
                    ])]
                })]
            })

    def test_17_check_attr_value_ids(self):
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_gasoline.id,
                'value_ids': [(6, 0, [
                    self.value_gasoline.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_diesel.id,
                'value_ids': [(6, 0, [
                    self.value_diesel.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_218i.id,
                'value_ids': [(6, 0, [
                    self.value_218i.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_220i.id,
                'value_ids': [(6, 0, [
                    self.value_220i.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_218d.id,
                'value_ids': [(6, 0, [
                    self.value_218d.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_220d.id,
                'value_ids': [(6, 0, [
                    self.value_220d.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_red.id,
                'value_ids': [(6, 0, [
                    self.value_red.id
                ])]
            })]
        })
        self.product_tmpl_id.write({
            'attribute_value_line_ids': [(0, 0, {
                'product_tmpl_id': self.product_tmpl_id.id,
                'value_id': self.value_silver.id,
                'value_ids': [(6, 0, [
                    self.value_silver.id
                ])]
            })]
        })
        with self.assertRaises(ValidationError):
            self.product_tmpl_id.write({
                'attribute_value_line_ids': [(0, 0, {
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'value_id': self.value_rims_378.id,
                    'value_ids': [(6, 0, [
                        self.value_rims_378.id
                    ])]
                })]
            })

    def test_18_check_duplicate_product(self):
        self.product_tmpl_id.configure_product()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id):
            self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id):
            self.value_218i.id,
            '__attribute-{}'.format(self.attr_color.id):
            self.value_red.id,
        })
        product_config_wizard.action_next_step()
        with self.assertRaises(ValidationError):
            self.env['product.product'].create({
                'name': 'Test Configuration',
                'product_tmpl_id': self.product_tmpl_id.id,
                'attribute_value_ids': [(6, 0, [
                    self.value_gasoline.id,
                    self.value_218i.id,
                    self.value_red.id
                ])]
            })

    def test_19_fields_view_get(self):
        product_product = self._get_product_id()
        product_product.with_context({
            'default_config_ok': True}).fields_view_get()

    def test_20_get_conversions_dict(self):
        product_product = self._get_product_id()
        product_product._get_conversions_dict()

    def test_21_compute_product_variant_count(self):
        self.product_tmpl_id = self.env['product.template'].create({
            'name': 'Test Configuration',
            'config_ok': True,
            'type': 'consu',
            'categ_id': self.product_category.id,
        })
        product_variant_count = \
            self.product_tmpl_id.product_variant_count
        self.assertEqual(
            product_variant_count,
            1,
            'Error: If not equal\
            Method: _compute_product_variant_count()'
        )

    def test_22_get_config_name(self):
        product_product = self._get_product_id()
        product_product._get_config_name()
        self.assertTrue(
            product_product.name,
            'Error: If value False\
            Method: _get_config_name()'
        )

    def test_23_search_product_weight(self):
        product_product = self._get_product_id()
        operator = 'and'
        value = 10
        search_product_weight = \
            product_product._search_product_weight(operator, value)
        self.assertTrue(
            search_product_weight,
            'Error: If value False\
            Method: _search_product_weight()'
        )

    def test_24_search_weight(self):
        operator = 'and'
        value = 10
        search_weight = \
            self.product_tmpl_id._search_weight(operator, value)
        self.assertTrue(
            search_weight,
            'Error: If value False\
            Method: _search_weight()'
        )
