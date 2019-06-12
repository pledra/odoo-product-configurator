from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class ProductConfig(TransactionCase):

    def setUp(self):
        super(ProductConfig, self).setUp()
        self.productConfigDomain = self.env['product.config.domain']
        self.config_product_1 = self.env.ref(
            'product_configurator.product_config_line_gasoline_engines')
        self.config_product_2 = self.env.ref(
            'product_configurator.2_series_config_step_body')
        self.config_session_1 = self.env['product.config.session']
        self.config_step_1 = self.env.ref(
            'product_configurator.config_step_extras')
        self.ProductConfWizard = self.env['product.configurator']
        self.config_product = self.env.ref('product_configurator.bmw_2_series')
        self.product_category = self.env.ref('product.product_category_5')
        self.config_custom_val = self.env['product.config.session.custom.value']
        self.res_user_id = self.env.ref('base.user_demo')
        self.AttachmentId = self.env.ref('product_configurator.attachment_1')

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

    # TODO :: Left to take review of code
    def test_00_check_value_attributes(self):
        self.config_product_1.attribute_line_id = 6
        self.config_product_1.attribute_line_id.attribute_id = 9
        self.assertNotEqual(
            self.config_product_1.attribute_line_id,
            self.config_product_1.attribute_line_id.attribute_id,
            'Id not Equal'
        )
        with self.assertRaises(ValidationError):
            self.config_product_1.check_value_attributes()

    def test_01_check_config_step(self):
        with self.assertRaises(ValidationError):
            self.config_product_2.config_step_id = 4

    def test_02_compute_config_step_name(self):
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
            '__attribute-{}'.format(self.attr_options.id): [
                [6, 0, [self.value_options_1.id, self.value_options_2.id]]]
        })
        product_config_wizard.action_next_step()
        
        self.config_session_1._compute_config_step_name()
        config_session_id = self.config_session_1.search([(
            'product_tmpl_id', '=', self.config_product.id)])

        self.value_gasoline.price_ids.weight_extra = 34
        self.config_session_1.get_cfg_weight()
        self.value_gasoline = self.value_gasoline.with_context(active_id=self.config_product.id)
        self.config_session_1.flatten_val_ids(config_session_id.value_ids)
        self.assertEqual(
            self.value_gasoline.price_ids.weight_extra,
            self.value_gasoline.weight_extra,
            'values not set'
        )

        self.value_gasoline.price_ids.price_extra = 35
        self.config_session_1.get_cfg_price()
        self.value_gasoline = self.value_gasoline.with_context(active_id=self.config_product.id)
        self.config_session_1.flatten_val_ids(config_session_id.value_ids)
        self.assertEqual(
            self.value_gasoline.price_ids.price_extra,
            self.value_gasoline.price_extra,
            'values not set'
        )

        self.assertEqual(
            self.config_step_1.name,
            config_session_id.config_step_name,
            'Names are Equal'
        )
        productConfigDomainId = self.productConfigDomain.create({
            'name': 'Restriction1'
        })
        self.domainConfigDomainLine = self.env['product.config.domain.line'].create({
            'attribute_id': self.attr_color.id,
            'condition': 'in',
            'value_ids': [(6, 0, [self.value_red.id])],
            'operator': 'and',
            'domain_id': productConfigDomainId.id,
        })
        self.productConfigLine = self.env['product.config.line'].create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_engine.id,
            'attribute_line_id': self.env.ref('product_configurator.product_attribute_line_2_series_engine').id,
            'value_ids': [(6, 0, [
                self.env.ref('product_configurator.product_attribute_value_218i').id,
                self.env.ref('product_configurator.product_attribute_value_220i').id,
                self.env.ref('product_configurator.product_attribute_value_228i').id,
                self.env.ref('product_configurator.product_attribute_value_m235i').id,
                self.env.ref('product_configurator.product_attribute_value_m235i_xdrive').id])],
            'domain_id': productConfigDomainId.id,
        })

        config_session = self.config_session_1.create({
            'product_tmpl_id': self.config_product.id,
            'user_id': self.res_user_id.id,
            'state': 'draft',
        })
        config_custom_values = self.config_custom_val.create({
            'attribute_id': self.attr_engine.id,
            'cfg_session_id': config_session.id,
            'value': 'car',
        })
        # self.attr_engine.custom_type = 'int'
        # update_val = config_custom_values.update({'value': 123})
        # config_val = config_session._get_custom_vals_dict()
        # self.assertEqual(
        #     config_custom_values.value,
        #     config_val,
        #     'not equal'
        # )
        # self.attr_engine.custom_type = 'binary'
        # 'attachment_ids': [(6, 0, [self.AttachmentId.id])],
        # config_custom_values.update({'attachment_ids': [(6, 0, [self.AttachmentId.id])]})
        # config_session._get_custom_vals_dict()
        # self.assertEqual(
        #     config_custom_values.attachment_ids,
        #     0,
        #     'not equal'
        # )
        # self.attr_engine.custom_type = 'char'
        # config_custom_values.update({'value': 'abc'})
        # config_session._get_custom_vals_dict()
        # self.assertEqual(
        #     config_custom_values.value,
        #     abc,
        #     'not equal'
        # )