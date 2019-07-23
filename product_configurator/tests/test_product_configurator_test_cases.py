from odoo.tests.common import TransactionCase


class ProductConfiguratorTestCases(TransactionCase):

    def setUp(self):
        super(ProductConfiguratorTestCases, self).setUp()

        self.ProductConfWizard = self.env['product.configurator']
        self.config_product = self.env.ref('product_configurator.bmw_2_series')
        self.product_category = self.env.ref('product.product_category_5')

        # attributes
        self.attr_fuel = self.env.ref(
            'product_configurator.product_attribute_fuel')
        self.attr_engine = self.env.ref(
            'product_configurator.product_attribute_engine')
        self.attr_color = self.env.ref(
            'product_configurator.product_attribute_color')
        self.attr_rims = self.env.ref(
            'product_configurator.product_attribute_rims')
        self.attr_model_line = self.env.ref(
            'product_configurator.product_attribute_model_line')
        self.attr_tapistry = self.env.ref(
            'product_configurator.product_attribute_tapistry')
        self.attr_transmission = self.env.ref(
            'product_configurator.product_attribute_transmission')
        self.attr_options = self.env.ref(
            'product_configurator.product_attribute_options')

        # values
        self.value_gasoline = self.env.ref(
            'product_configurator.product_attribute_value_gasoline')
        self.value_218i = self.env.ref(
            'product_configurator.product_attribute_value_218i')
        self.value_220i = self.env.ref(
            'product_configurator.product_attribute_value_220i')
        self.value_red = self.env.ref(
            'product_configurator.product_attribute_value_red')
        self.value_rims_378 = self.env.ref(
            'product_configurator.product_attribute_value_rims_378')
        self.value_sport_line = self.env.ref(
            'product_configurator.product_attribute_value_sport_line')
        self.value_model_sport_line = self.env.ref(
            'product_configurator.product_attribute_value_model_sport_line')
        self.value_tapistry = self.env.ref(
            'product_configurator.product_attribute_value_tapistry' +
            '_oyster_black')
        self.value_transmission = self.env.ref(
            'product_configurator.product_attribute_value_steptronic')
        self.value_options_1 = self.env.ref(
            'product_configurator.product_attribute_value_smoker_package')
        self.value_options_2 = self.env.ref(
            'product_configurator.product_attribute_value_sunroof')

    def _configure_product_nxt_step(self):
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': self.config_product.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
            '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
            '__attribute-{}'.format(self.attr_rims.id): self.value_rims_378.id
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_sport_line.id,
        })
        product_config_wizard.action_previous_step()
        product_config_wizard.action_previous_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attr_engine.id): self.value_220i.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(
                self.attr_model_line.id): self.value_model_sport_line.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(
                self.attr_tapistry.id): self.value_tapistry.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(
                self.attr_transmission.id): self.value_transmission.id,
            '__attribute-{}'.format(
                self.attr_options.id): [[6, 0, [self.value_options_2.id]]],
        })

        return product_config_wizard.action_next_step()
