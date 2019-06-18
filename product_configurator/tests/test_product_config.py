from odoo.addons.product_configurator.tests.\
    product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.exceptions import ValidationError
from ast import literal_eval


class ProductConfig(ProductConfiguratorTestCases):

    def setUp(self):
        super(ProductConfig, self).setUp()
        self.productConfWizard = self.env['product.configurator']
        self.productTemplate = self.env['product.template']
        self.productAttribute = self.env['product.attribute']
        self.productAttributeVals = self.env['product.attribute.value']
        self.productAttributeLine = self.env['product.attribute.line']
        self.productConfigSession = self.env['product.config.session']
        self.productConfigDomain = self.env['product.config.domain']
        self.config_product = self.env.ref('product_configurator.bmw_2_series')
        self.attr_engine = self.env.ref(
            'product_configurator.product_attribute_engine')
        self.config_product_1 = self.env.ref(
            'product_configurator.product_config_line_gasoline_engines')
        self.config_product_2 = self.env.ref(
            'product_configurator.2_series_config_step_body')
        # domain
        self.domain_gasolin = self.env.ref(
            'product_configurator.product_config_domain_gasoline')
        self.domain_engine = self.env.ref(
            'product_configurator.product_config_domain_diesel')
        self.config_image_red = self.env.ref(
            'product_configurator.config_image_1')
        # value
        self.value_gasoline = self.env.ref(
             'product_configurator.product_attribute_value_gasoline')
        self.value_diesel = self.env.ref(
            'product_configurator.product_attribute_value_diesel')
        self.value_red = self.env.ref(
            'product_configurator.product_attribute_value_red')
        # config_step
        self.config_step_engine = self.env.ref(
            'product_configurator.config_step_engine')
        self.attribute_line = self.env.ref(
            'product_configurator.product_attribute_line_2_series_engine')
        self.value_silver = self.env.ref(
            'product_configurator.product_attribute_value_silver')
        self.value_rims_387 = self.env.ref(
            'product_configurator.product_attribute_value_rims_387'),
        # attribute line
        self.attribute_line_2_series_rims = self.env.ref(
            'product_configurator.product_attribute_line_2_series_rims')
        self.attribute_line_2_series_tapistry = self.env.ref(
            'product_configurator.product_attribute_line_2_series_tapistry')
        self.attribute_value_tapistry_oyster_black = \
            self.env.ref(
                'product_configurator.product_attribute_value_tapistry_oyster_black')
        self.attribute_line_2_series_transmission = self.env.ref(
            'product_configurator.product_attribute_line_2_series_transmission'
        )

        # session id
        self.session_id = self.productConfigSession.create({
            'product_tmpl_id': self.config_product.id,
            'value_ids': [(6, 0, [
                self.value_gasoline.id,
                self.value_transmission.id,
                self.value_red.id]
            )],
            'user_id': self.env.user.id,
        })
        # ir attachment
        self.irAttachement = self.env['ir.attachment'].create({
            'name': 'Test attachement',
        })

        # configure product
        self._configure_product_nxt_step()
        self.config_session = self.productConfigSession.search([
            ('product_tmpl_id', '=', self.config_product.id)])

        # create product template
        self.product_tmpl_id = self.productTemplate.create({
            'name': 'Coca-Cola'
        })
        # create attribute 1
        self.attribute_1 = self.productAttribute.create({
            'name': 'Color',
        })
        # create attribute 2
        self.attribute_2 = self.productAttribute.create({
            'name': 'Flavour',
        })

        # create attribute value 1
        self.attribute_vals_1 = self.productAttributeVals.create({
            'name': 'Orange',
            'attribute_id': self.attribute_1.id,
        })
        # create attribute value 2
        self.attribute_vals_2 = self.productAttributeVals.create({
            'name': 'Balck',
            'attribute_id': self.attribute_1.id,
        })
        # create attribute value 3
        self.attribute_vals_3 = self.productAttributeVals.create({
            'name': 'Coke',
            'attribute_id': self.attribute_2.id,
        })
        # create attribute value 4
        self.attribute_vals_4 = self.productAttributeVals.create({
            'name': 'Mango',
            'attribute_id': self.attribute_2.id,
        })

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

    def test_02_get_trans_implied(self):
        self.domain_gasolin.write({
            'implied_ids': [(6, 0, [self.domain_engine.id])]
        })
        trans_implied_ids = self.domain_gasolin.trans_implied_ids.ids
        self.assertEqual(
            trans_implied_ids[-1],
            self.domain_engine.id,
            'Error: If value not exists\
            Method: _get_trans_implied()'
        )

    def test_03_check_value_attributes(self):
        with self.assertRaises(ValidationError):
            self.config_product.config_line_ids.write({
                'attribute_line_id': self.attr_engine.id,
                'value_ids': [(6, 0, [self.value_gasoline.id])]
            })

    def test_04_check_config_step(self):
        with self.assertRaises(ValidationError):
            self.env['product.config.step.line'].create({
                'product_tmpl_id': self.config_product.id,
                'config_step_id': self.config_step_engine.id,
                'attribute_line_ids': [(6, 0, [self.attribute_line.id])]
            })

    def test_05_compute_cfg_price(self):
        # check for _compute_cfg_price
        self.assertEqual(
            self.session_id.price,
            self.config_product.list_price,
            'Error: If different session price and list_price\
            Method: _compute_cfg_price'
        )

    def test_06_get_custom_vals_dict(self):
        # check for _get_custom_vals_dict
        productConfigSessionCustVals = self.env[
            'product.config.session.custom.value'].create({
                'cfg_session_id': self.session_id.id,
                'attribute_id': self.attr_fuel.id,
                'value': 'fuel vals'
            })
        checkCharval = self.session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkCharval.values())[0],
            productConfigSessionCustVals.value,
            'Error: If Not Char value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Int
        self.attr_fuel.custom_type = 'int'
        productConfigSessionCustVals.update({'value': 154})
        checkIntval = self.session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkIntval.values())[0],
            literal_eval(productConfigSessionCustVals.value),
            'Error: If Not Integer value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Float
        self.attr_fuel.custom_type = 'float'
        productConfigSessionCustVals.update({'value': 94.5})
        checkFloatval = self.session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkFloatval.values())[0],
            literal_eval(productConfigSessionCustVals.value),
            'Error: If Not Float value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Binary
        self.attr_color.custom_type = 'binary'
        productConfigSessionCustVals1 = self.env[
            'product.config.session.custom.value'].create({
                'cfg_session_id': self.session_id.id,
                'attribute_id': self.attr_color.id,
                'attachment_ids': [(6, 0, [self.irAttachement.id])]
            })
        checkBinaryval = self.session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkBinaryval.values())[1],
            productConfigSessionCustVals1.attachment_ids,
            'Error: If Not attachement\
            Method: _get_custom_vals_dict()'
        )

    def test_07_compute_config_step_name(self):
        self.assertTrue(
            self.config_session.config_step_name,
            'Error: If not config step name\
            Method: _compute_config_step_name()'
        )

    def test_09_search_variant(self):
        with self.assertRaises(ValidationError):
            self.env['product.config.session'].search_variant()

        # check for search duplicate variant
        variant_id = self.config_product.product_variant_ids
        checkSearchvarient = self.config_session.search_variant()
        self.assertEqual(
            checkSearchvarient,
            variant_id,
            'Error: If Not Equal Variant or False\
            Method: search_variant()'
        )

    def test_10_check_custom_type(self):
        # check for check_custom_type
        with self.assertRaises(ValidationError):
            self.env['product.config.session.custom.value'].create({
                'attribute_id': self.value_silver.attribute_id.id,
                'cfg_session_id': self.config_session.id,
                'value': 'Test',
                'attachment_ids': [(6, 0, [self.irAttachement.id])],
            })

        self.attr_color.custom_type = 'binary'
        with self.assertRaises(ValidationError):
            self.env['product.config.session.custom.value'].create({
                'attribute_id': self.value_silver.attribute_id.id,
                'cfg_session_id': self.config_session.id,
                'value': 'Test',
                'attachment_ids': [(6, 0, [self.irAttachement.id])],
            })

    def test_11_create_get_variant(self):
        # configure new product to check for search not dublicate variant
        self.attributeLine1 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attribute_1.id,
            'value_ids': [(6, 0, [
                           self.attribute_vals_1.id,
                           self.attribute_vals_2.id])]
        })
        # create attribute line 2
        self.attributeLine2 = self.productAttributeLine.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_id': self.attribute_2.id,
            'value_ids': [(6, 0, [
                           self.attribute_vals_3.id,
                           self.attribute_vals_4.id])]
        })
        self.product_tmpl_id.write({
            'attribute_line_ids': [(6, 0, [
                                    self.attributeLine1.id,
                                    self.attributeLine2.id])],
        })
        self.product_tmpl_id.configure_product()
        self.productConfWizard.action_next_step()
        product_config_wizard = self.productConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attribute_1.id):
            self.attribute_vals_1.id,
            '__attribute-{}'.format(self.attribute_2.id):
            self.attribute_vals_3.id
        })
        product_config_wizard.action_next_step()
        config_session_1 = self.productConfigSession.search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id)])
        createVarientId = config_session_1.create_get_variant()
        self.assertEqual(
            createVarientId.name,
            self.product_tmpl_id.name,
            'Error: If Not Equal variant name\
            Method: search_variant()'
        )
        self.attributeLine1.custom = True
        self.env['product.config.session.custom.value'].create({
            'cfg_session_id': config_session_1.id,
            'attribute_id': self.attribute_1.id,
            'value': 'Coke'
        })
        config_session_1.create_get_variant()

    def test_12_check_value_ids(self):
        with self.assertRaises(ValidationError):
            self.config_image_red.write({
                'value_ids': [(6, 0, [
                    self.value_gasoline.id,
                    self.value_diesel.id])]
            })

    def test_13_unique_attribute(self):
        with self.assertRaises(ValidationError):
            self.env['product.config.session.custom.value'].create({
                'cfg_session_id': self.config_session.id,
                'attribute_id': self.attr_engine.id,
                'value': '1234'
            })
            self.env['product.config.session.custom.value'].create({
                'cfg_session_id': self.config_session.id,
                'attribute_id': self.attr_engine.id,
                'value': '1234'
            })

    def test_14_compute_domain(self):
        productConfigDomainId = self.productConfigDomain.create({
            'name': 'Restriction1'
        })
        self.productConfigDomainLine = self.env[
            'product.config.domain.line'].create({
                'attribute_id': self.attr_color.id,
                'condition': 'in',
                'value_ids': [(6, 0, [self.value_red.id])],
                'operator': 'and',
                'domain_id': productConfigDomainId.id,
            })
        self.productConfigLine = self.env['product.config.line'].create({
            'product_tmpl_id': self.config_product.id,
            'attribute_id': self.attr_engine.id,
            'attribute_line_id': self.env.ref(
                'product_configurator.product_attribute_line_2_series_engine'
            ).id,
            'value_ids': [(6, 0, [
                self.env.ref(
                    'product_configurator.product_attribute_value_218i').id,
                self.env.ref(
                    'product_configurator.product_attribute_value_220i').id,
                self.env.ref(
                    'product_configurator.product_attribute_value_228i').id,
                self.env.ref(
                    'product_configurator.product_attribute_value_m235i').id,
                self.env.ref(
                    'product_configurator.product_attribute_value_m235i_xdrive'
                ).id])],
            'domain_id': productConfigDomainId.id,
        })
        self.assertTrue(
            self.productConfigDomainLine,
            'Exsits'
        )
