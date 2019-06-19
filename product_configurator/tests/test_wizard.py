from ..tests.product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.exceptions import ValidationError, UserError


class ConfigurationWizard(ProductConfiguratorTestCases):

    def setUp(self):
        super(ConfigurationWizard, self).setUp()
        self.productTemplate = self.env['product.template']
        self.productAttributeLine = self.env['product.attribute.line']
        self.productConfigStepLine = self.env['product.config.step.line']
        self.productConfigSession = self.env['product.config.session']
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
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')
        self.attr_vals = attribute_vals

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().items()
        }

    def get_attr_val_ids(self, ext_ids):
        """Return a list of database ids using the external_ids
        passed via ext_ids argument"""

        value_ids = []

        attr_val_prefix = 'product_configurator.product_attribute_value_%s'

        for ext_id in ext_ids:
            if ext_id in self.attr_val_ext_ids:
                value_ids.append(self.attr_val_ext_ids[ext_id])
            elif attr_val_prefix % ext_id in self.attr_val_ext_ids:
                value_ids.append(
                    self.attr_val_ext_ids[attr_val_prefix % ext_id]
                )

        return value_ids

    def create_wizard(self, product_tmpl=None):
        if not product_tmpl:
            product_tmpl = self.cfg_tmpl
        wizard_vals = {
            'product_tmpl_id': product_tmpl.id
        }
        wizard = self.env['product.configurator'].create(vals=wizard_vals)
        return wizard

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

    def test_00_action_next_step(self):
        self.ProductConfWizard.action_next_step()
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': self.product_tmpl_id.id,
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
        product_config_wizard.action_next_step()
        self.assertEqual(
            product_config_wizard.state,
            'configure',
            'Error: If wizard not in configure state\
            Method: action_next_step()'
        )
        with self.assertRaises(UserError):
            product_config_wizard.action_next_step()

        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218d.id,
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        wizard_action = product_config_wizard.action_next_step()
        varient_id = wizard_action.get('res_id')
        self.assertTrue(
            varient_id,
            'Error: if varient id not exists\
            Method: action_next_step()'
        )

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

        # configure product
        product_config_wizard.action_next_step()
        config_session = self.productConfigSession.search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id)])
        self.assertEqual(
            product_config_wizard.state,
            config_session.config_step,
            'Error: If state are not equal\
            Method: action_next_step()'
        )
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
        })
        action = product_config_wizard.action_next_step()
        new_variant = action.get('res_id')
        self.assertTrue(
            new_variant,
            'Error: if new varient id not exists\
            Method: action_next_step()'
        )

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
