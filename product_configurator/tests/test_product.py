from odoo.addons.product_configurator.tests.\
    product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestProduct(ProductConfiguratorTestCases):

    def setUp(self):
        super(TestProduct, self).setUp()
        self.productAttributeLine = self.env['product.attribute.line']
        self.value_diesel = self.env.ref(
            'product_configurator.product_attribute_value_diesel')
        self.value_218d = self.env.ref(
            'product_configurator.product_attribute_value_218d')
        self.value_220d = self.env.ref(
            'product_configurator.product_attribute_value_220d')
        # self.value_220d_xdrive = self.env.ref(
        #     'product_configurator.product_attribute_value_220d_xdrive')
        # self.value_225d = self.env.ref(
        #     'product_configurator.product_attribute_value_225d')
        # self.value_luxury_line = self.env.ref(
        #     'product_configurator.product_attribute_value_luxury_line')
        # self.value_value_model_luxury_line = self.env.ref(
        #     'product_configurator.product_attribute_value_model_luxury_line')
        # self.value_model_m_sport = self.env.ref(
        #     'product_configurator.product_attribute_value_model_m_sport')
        # self.value_model_advantage = self.env.ref(
        #     'product_configurator.product_attribute_value_model_advantage')
        self.value_silver = self.env.ref(
            'product_configurator.product_attribute_value_silver')
        # self.value_black = self.env.ref(
        #     'product_configurator.product_attribute_value_black')
        # self.value_rims_378 = self.env.ref(
        #     'product_configurator.product_attribute_value_rims_378')\
        # self.value_rims_387 = self.env.ref(
        #     'product_configurator.product_attribute_value_rims_387')
        # self.value_rims_384 = self.env.ref(
        #     'product_configurator.product_attribute_value_rims_384')
        # self.value_tapistry_black = self.env.ref(
        #     'product_configurator.product_attribute_value_tapistry_black')
        # self.value_tapistry_oyster_black = self.env.ref(
        #     'product_configurator.product_attribute_value_tapistry_oyster_black')
        # self.value_tapistry_coral_red_black = self.env.ref(
        #     'product_configurator.product_attribute_value_tapistry_coral_red_black')
        # # self.value_steptronic = self.env.ref(
        # #     'product_configurator.product_attribute_value_steptronic')
        # self.value_steptronic_sport = self.env.ref(
        #     'product_configurator.product_attribute_value_steptronic_sport')
        # self.value_armrest = self.env.ref(
        #     'product_configurator.product_attribute_value_armrest')
        # # self.value_smoker_package = self.env.ref(
        # #     'product_configurator.product_attribute_value_smoker_package')
        # # self.value_sunroof = self.env.ref(
        # #     'product_configurator.product_attribute_value_sunroof')
        # self.value_tow_hook = self.env.ref(
        #     'product_configurator.product_attribute_value_tow_hook')



    def test_00_compute_template_attr_vals(self):
        # create attribute line 1
        self.attributeLine1 = self.productAttributeLine.create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_fuel.id,
            'value_ids': [(6, 0, [
                           self.value_gasoline.id,
                           self.value_diesel.id])],
            'required': True,
        })
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218i.id,
                           self.value_220i.id])],
            'required': True,
        })
        # create attribute line 2
        self.attributeLine3 = self.productAttributeLine.create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_engine.id,
            'value_ids': [(6, 0, [
                           self.value_218d.id,
                           self.value_220d.id])],
            'required': True,
        })
        # create attribute line 1
        self.attributeLine4 = self.productAttributeLine.create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_color.id,
            'value_ids': [(6, 0, [
                           self.value_red.id,
                           self.value_silver.id])],
            'required': True,
        })
        self.config_product.write({
            'attribute_line_ids': [(6, 0, [
                                    self.attributeLine1.id,
                                    self.attributeLine2.id,
                                    self.attributeLine3.id,
                                    self.attributeLine4.id])],
        })
        value_ids = self.config_product.attribute_line_ids.mapped('value_ids')
        self.config_product._compute_template_attr_vals()
        self.assertEqual(
            value_ids,
            self.config_product.attribute_line_val_ids,
            'Error: if value are different\
            Method: _compute_template_attr_vals() '
        )

        # print("\n\n\n -------self.productConfigDomainId-----", self.productConfigDomainId.id)
        # # create attribute value line 1
        # self.productConfigDomainLineId = self.env['product.config.domain.line'].create({
        #     'domain_id': self.productConfigDomainId.id,
        #     'attribute_id': self.attr_fuel.id,
        #     'condition': 'in',
        #     'value_ids': [(6, 0, [self.value_gasoline.id])],
        #     'operator': 'and',
        # })
        # self.productConfigLine = self.env['product.config.line'].create({
        #     'product_tmpl_id': self.config_product.id,
        #     'attribute_line_id': self.attr_engine.id,
        #     'value_ids': [(6, 0, [
        #         self.value_218i.id,
        #         self.value_220i.id])],
        #     'domain_id': self.productConfigDomainLineId.id,
        # })
        # self.attribute_value_line_1 = self.productAttributeValueLine.create({
        #     'config_product': self.config_product.id,
        #     'value_id': self.attribute_vals_1.id,
        #     'value_ids': [(6, 0, [
        #                     self.attribute_vals_1.id,
        #                     self.attribute_vals_3.id])],
        # })
        # self.config_product.write({
        #     'config_line_ids': [(0, 0, [])],
        # })
        self.config_product.weight=120
        self.assertEqual(
            self.config_product.weight,
            self.config_product.weight_dummy,
            'Error: If set diffrent value for dummy_weight\
            Method: _set_weight()'
        )
        self.config_product.weight_dummy = 50.0
        self.config_product._compute_weight()
        self.assertEqual(
            self.config_product.weight_dummy,
            self.config_product.weight,
            'Error: If set diffrent value for weight\
            Method: _compute_weight()'
        )
        attribute_value_action = self.config_product.get_product_attribute_values_action()
        contextValue = attribute_value_action.get('context')
        self.assertEqual(
            contextValue['active_id'],
            self.config_product.id,
            'Error: If different template id\
            Method: get_product_attribute_values_action()'
        )
        self.config_product.config_ok = False
        self.assertFalse(
            self.config_product.config_ok,
            'Error: If Boolean False\
            Method: toggle_config()'
        )
        # # self.config_product.config_ok = True
        # self.config_product.toggle_config()
        # varient_value = self.config_product.create_variant_ids()
        # self.assertIsNone(
        #     varient_value,
        #     'Error: If its return True\
        #     Method: create_variant_ids()'
        # )
        # varient_value2 = self.config_product.toggle_config()
        # self.assertTrue(
        #     varient_value2,
        #     'Error: If its return none\
        #     Method: create_variant_ids()'
        # )
        # # self.config_product.toggle_config()
        # product_config_wizard.action_previous_step()
        # product_config_wizard.action_previous_step()
        # product_config_wizard.write({
        #     '__attribute-{}'.format(self.attr_engine.id): self.value_220i.id,
        # })
        # product_config_wizard.action_next_step()
        # product_config_wizard.action_next_step()
        # product_config_wizard.write({
        #     '__attribute-{}'.format(
        #         self.attr_model_line.id): self.value_model_sport_line.id,
        # })
        # product_config_wizard.action_next_step()
        # product_config_wizard.write({
        #     '__attribute-{}'.format(
        #         self.attr_tapistry.id): self.value_tapistry.id,
        # })
        # value_ids = self.value_gasoline + self.value_220i + self.value_red\
        #     + self.value_rims_378 + self.value_model_sport_line\
        #     + self.value_tapistry + self.value_transmission\
        #     + self.value_options_1 + self.value_options_2
        # new_variant = self.config_product.product_variant_ids.filtered(
        #     lambda variant:
        #     variant.attribute_value_ids
        #     == value_ids
        # )
        print("\n\n\n\n -----------new_variant", self.config_product.product_variant_ids)