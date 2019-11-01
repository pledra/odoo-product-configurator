from ..tests.test_product_configurator_test_cases import \
    ProductConfiguratorTestCases
from odoo.exceptions import UserError


class ConfigurationWizard(ProductConfiguratorTestCases):

    def setUp(self):
        super(ConfigurationWizard, self).setUp()
        self.productTemplate = self.env['product.template']
        self.productAttributeLine = self.env['product.template.attribute.line']
        self.productConfigStepLine = self.env['product.config.step.line']
        self.productConfigSession = self.env['product.config.session']
        self.product_category = self.env.ref('product.product_category_5')
        self.attr_line_fuel = self.env.ref(
            'product_configurator.product_attribute_line_2_series_fuel')
        self.attr_line_engine = self.env.ref(
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
        self.custom_vals = self.productConfigSession.get_custom_value_id()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')
        self.attr_vals = attribute_vals

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().items()
        }

    def _check_wizard_nxt_step(self):
        self.ProductConfWizard.action_next_step()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': self.product_tmpl_id.id,
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
        # configure product creating config step
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
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        return product_config_wizard

    def test_01_action_previous_step(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.action_previous_step()
        self.assertEqual(
            product_config_wizard.state,
            str(self.configStepLine1.id),
            'Error: If state are not equal\
            Method: action_next_step()'
        )
        product_config_wizard.action_next_step()
        self.assertEqual(
            product_config_wizard.state,
            str(self.configStepLine2.id),
            'Error: If state are not equal\
            Method: action_next_step()'
        )
        wizard_action = product_config_wizard.action_next_step()
        variant_id2 = wizard_action.get('res_id')
        self.assertTrue(
            variant_id2,
            'Error: If varient not exists\
            Method: action_next_step()'
        )

    def test_02_action_reset(self):
        product_config_wizard = self._check_wizard_nxt_step()
        action_wizard = product_config_wizard.action_reset()
        product_tmpl_id = action_wizard.get('context')
        self.assertTrue(
            product_tmpl_id.get('default_product_tmpl_id'),
            'Error: If product_tmpl_id not exists\
            Method: action_reset()'
        )

    def test_03_compute_attr_lines(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._compute_attr_lines()
        self.assertTrue(
            product_config_wizard.attribute_line_ids,
            'Error: If atttribute_line_ids not exists\
            Method: _compute_attr_lines()'
        )

    def test_04_get_state_selection(self):
        product_config_wizard = self._check_wizard_nxt_step()
        config_wiz = product_config_wizard.with_context(
            {'wizard_id': product_config_wizard.id}).get_state_selection()
        self.assertTrue(
            config_wiz[1:],
            'Error: If not config step selection\
            Method: get_state_selection()'
        )

    def test_05_compute_cfg_image(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._compute_cfg_image()
        self.assertFalse(
            product_config_wizard.product_img,
            'Error: If product_img exists\
            Method: _compute_cfg_image()'
        )

    def test_06_onchange_product_tmpl(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.write({
            'product_tmpl_id': self.config_product.id,
        })
        with self.assertRaises(UserError):
            product_config_wizard.onchange_product_tmpl()

    def test_07_get_onchange_domains(self):
        product_config_wizard = self._check_wizard_nxt_step()
        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]
        values = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]
        product_config_wizard.get_onchange_domains(values, conf)

    def test_08_onchange_state(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._onchange_state()

    def test_09_onchange_product_preset(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard._onchange_product_preset()

    def test_10_open_step(self):
        wizard = self.env['product.configurator']
        step_to_open = wizard.config_session_id.\
            check_and_open_incomplete_step()
        wizard.open_step(step_to_open)

    def test_11_onchange(self):
        field_name = ''
        values = {
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id
        }
        product_config_wizard = self._check_wizard_nxt_step()
        field_prefix = product_config_wizard._prefixes.get('field_prefix')
        field_name = '%s%s' % (field_prefix, field_name)
        specs = product_config_wizard._onchange_spec()
        product_config_wizard.onchange(values, field_name, specs)

        product_config_wizard.attribute_line_ids.update({
            'attribute_id': self.attr_fuel.id,
            'custom': True,
        })
        values2 = {
            '__attribute-{}'.format(self.attr_fuel.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_fuel.id): 'Test1',
        }
        product_config_wizard.onchange(values2, field_name, specs)

    def test_12_fields_get(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.fields_get()
        product_config_wizard.with_context({
            'wizard_id': product_config_wizard.id}).fields_get()

        # custom value
        self.attr_line_fuel.custom = True
        self.attr_line_engine.custom = True
        product_config_wizard_1 = self.ProductConfWizard.create({
            'product_tmpl_id': self.config_product.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__custom-{}'.format(self.attr_fuel.id): 'Test1',
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__custom-{}'.format(self.attr_engine.id): 'Test2',
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
            '__attribute-{}'.format(self.attr_rims.id): self.value_rims_378.id
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_sport_line.id,
        })
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_engine.id): self.value_220i.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_model_sport_line.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_tapistry.id): self.value_tapistry.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_transmission.id): self.value_transmission.id,
            '__attribute-{}'.format(
                self.attr_options.id): [[6, 0, [self.value_options_2.id]]],
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.with_context({
            'wizard_id': product_config_wizard_1.id}).fields_get()

    def test_13_fields_view_get(self):
        product_config_wizard = self._check_wizard_nxt_step()
        product_config_wizard.fields_view_get()
        product_config_wizard.with_context({
            'wizard_id': product_config_wizard.id}).fields_view_get()
        # custom value
        # custom value
        self.attr_line_fuel.custom = True
        self.attr_line_engine.custom = True
        product_config_wizard_1 = self.ProductConfWizard.create({
            'product_tmpl_id': self.config_product.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__custom-{}'.format(self.attr_fuel.id): 'Test1',
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__custom-{}'.format(self.attr_engine.id): 'Test2',
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
            '__attribute-{}'.format(self.attr_rims.id): self.value_rims_378.id
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_sport_line.id,
        })
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.action_previous_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_engine.id): self.value_220i.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_model_sport_line.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_tapistry.id): self.value_tapistry.id,
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(
                self.attr_transmission.id): self.value_transmission.id,
            '__attribute-{}'.format(
                self.attr_options.id): [[6, 0, [self.value_options_2.id]]],
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.with_context({
            'wizard_id': product_config_wizard_1.id}).fields_view_get()

    def test_14_unlink(self):
        product_config_wizard = self._check_wizard_nxt_step()
        unlinkWizard = product_config_wizard.unlink()
        self.assertTrue(
            unlinkWizard,
            'Error: If not unlink record\
            Method: unlink()'
        )

    def test_15_read(self):
        product_config_wizard = self._check_wizard_nxt_step()
        values = {
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        }
        product_config_wizard.read(values)
        product_tmpl = self.env['product.template'].create({
            'name': 'Test Custom',
            'config_ok': True,
            'type': 'consu',
            'categ_id': self.product_category.id,
        })
        self.ProductConfWizard.action_next_step()
        product_config_wizard_1 = self.ProductConfWizard.create({
            'product_tmpl_id': product_tmpl.id,
        })
        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create({
            'product_tmpl_id': product_tmpl.id,
            'attribute_id': self.attr_fuel.id,
            'value_ids': [(6, 0, [
                           self.value_gasoline.id,
                           self.value_diesel.id])],
            'required': True,
            'custom': True,
        })
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create({
            'product_tmpl_id': product_tmpl.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218i.id,
                           self.value_220i.id])],
            'required': True,
            'custom': True,
        })
        # create attribute line 2
        self.attributeLine3 = self.productAttributeLine.create({
            'product_tmpl_id': product_tmpl.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218d.id,
                           self.value_220d.id])],
            'required': True,
        })
        # configure product creating config step
        self.configStepLine1 = self.productConfigStepLine.create({
            'product_tmpl_id': product_tmpl.id,
            'config_step_id': self.config_step_engine.id,
            'attribute_line_ids': [(6, 0, [
                self.attributeLine1.id,
                self.attributeLine2.id])]
        })
        # create config_step_line 2
        self.configStepLine2 = self.productConfigStepLine.create({
            'product_tmpl_id': product_tmpl.id,
            'config_step_id': self.config_step_body.id,
            'attribute_line_ids': [(6, 0, [
                self.attributeLine3.id])]
        })
        product_tmpl.write({
            'config_step_line_ids': [(6, 0, [
                self.configStepLine1.id,
                self.configStepLine2.id]
            )],
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_fuel.id): "#DEFSRE",
            '__attribute-{}'.format(self.attr_engine.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_engine.id): "#FERDFGR",
        })
        product_config_wizard_1.action_next_step()
        product_config_wizard_1.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        # check for custom value
        custom_vals = {
            '__attribute-{}'.format(self.attr_fuel.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_fuel.id): "#DEFSRE",
            '__attribute-{}'.format(self.attr_engine.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_engine.id): "#FERDFGR",
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        }
        product_config_wizard_1.read(custom_vals)
        session = self.productConfigSession.search([
            ('product_tmpl_id', '=', product_tmpl.id)])
        session.unlink()
        self.attributeLine1.custom = False
        self.attributeLine1.multi = True
        self.ProductConfWizard.action_next_step()
        product_config_wizard_2 = self.ProductConfWizard.create({
            'product_tmpl_id': product_tmpl.id,
        })
        product_config_wizard_2.action_next_step()
        product_config_wizard_2.write({
            '__attribute-{}'.format(self.attr_fuel.id): [(6, 0, [
                self.value_diesel.id, self.value_gasoline.id])],
            '__attribute-{}'.format(self.attr_engine.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_engine.id): "#FERDFGR",
        })
        product_config_wizard_2.action_next_step()
        product_config_wizard_2.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        # check for multi value
        multi_vals = {
            '__attribute-{}'.format(self.attr_fuel.id): [(6, 0, [
                self.value_diesel.id, self.value_gasoline.id])],
            '__attribute-{}'.format(self.attr_engine.id): self.custom_vals.id,
            '__custom-{}'.format(self.attr_engine.id): "#FERDFGR",
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        }
        product_config_wizard_2.read(multi_vals)

    def test_16_get_onchange_domains(self):
        self.wizard = self.env['product.configurator']
        # session id
        session_id = self.productConfigSession.create({
            'product_tmpl_id': self.config_product.id,
            'value_ids': [(6, 0, [
                self.value_gasoline.id,
                self.value_transmission.id,
                self.value_red.id]
            )],
            'user_id': self.env.user.id,
        })
        field_prefix = self.wizard._prefixes.get('field_prefix')
        check_available_val_id = {
            field_prefix + '%s' % (self.value_gasoline.attribute_id.id):
            self.value_gasoline.id,
            field_prefix + '%s' % (self.value_218i.attribute_id.id):
            self.value_218i.id,
            field_prefix + '%s' % (self.value_sport_line.attribute_id.id):
            self.value_sport_line.id,
        }
        values_ids = self.value_diesel.ids
        product_tmpl_id = self.config_product
        domains_available = self.wizard.get_onchange_domains(
            check_available_val_id, values_ids, product_tmpl_id, session_id)
        rec = domains_available[field_prefix + str(
            self.value_sport_line.attribute_id.id)][-1][-1]
        self.assertNotIn(
            self.value_sport_line.id,
            rec,
            'Error: If value exists\
            Method: get_onchange_domains()'
            )
