from odoo.addons.product_configurator.tests.\
    product_configurator_test_cases import ProductConfiguratorTestCases
# from odoo.tests.common import TransactionCase
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

        self.config_product_1 = self.env.ref(
            'product_configurator.product_config_line_gasoline_engines')
        self.config_product_2 = self.env.ref(
            'product_configurator.2_series_config_step_body')

        # domain
        self.domain_gasolin = self.env.ref(
            'product_configurator.product_config_domain_gasoline')
        self.domain_engine = self.env.ref(
            'product_configurator.product_config_domain_diesel')

        # config_step
        self.config_step_engine = self.env.ref(
            'product_configurator.config_step_engine')
        self.attribute_line = self.env.ref('product_configurator.product_attribute_line_2_series_engine')
        self.value_silver = self.env.ref('product_configurator.product_attribute_value_silver')


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

    # def test_02_compute_config_step_name(self):
    #     product_config_wizard = self.ProductConfWizard.create({
    #         'product_tmpl_id': self.config_product.id,
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(self.attr_fuel.id): self.value_gasoline.id,
    #         '__attribute-{}'.format(self.attr_engine.id): self.value_218i.id
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(self.attr_color.id): self.value_red.id,
    #         '__attribute-{}'.format(self.attr_rims.id): self.value_rims_378.id
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(
    #             self.attr_model_line.id): self.value_sport_line.id,
    #     })
    #     product_config_wizard.action_previous_step()
    #     product_config_wizard.action_previous_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(self.attr_engine.id): self.value_220i.id,
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(
    #             self.attr_model_line.id): self.value_model_sport_line.id,
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(
    #             self.attr_tapistry.id): self.value_tapistry.id,
    #     })
    #     product_config_wizard.action_next_step()
    #     product_config_wizard.write({
    #         '__attribute-{}'.format(
    #             self.attr_transmission.id): self.value_transmission.id,
    #         '__attribute-{}'.format(self.attr_options.id): [
    #             [6, 0, [self.value_options_1.id, self.value_options_2.id]]]
    #     })
    #     product_config_wizard.action_next_step()

    #     self.config_session_1._compute_config_step_name()
    #     config_session_id = self.config_session_1.search([(
    #         'product_tmpl_id', '=', self.config_product.id)])

    #     self.value_gasoline.price_ids.weight_extra = 34
    #     self.config_session_1.get_cfg_weight()
    #     self.value_gasoline = self.value_gasoline.with_context(active_id=self.config_product.id)
    #     self.config_session_1.flatten_val_ids(config_session_id.value_ids)
    #     self.assertEqual(
    #         self.value_gasoline.price_ids.weight_extra,
    #         self.value_gasoline.weight_extra,
    #         'values not set'
    #     )

    #     self.value_gasoline.price_ids.price_extra = 35
    #     self.config_session_1.get_cfg_price()
    #     self.value_gasoline = self.value_gasoline.with_context(active_id=self.config_product.id)
    #     self.config_session_1.flatten_val_ids(config_session_id.value_ids)
    #     self.assertEqual(
    #         self.value_gasoline.price_ids.price_extra,
    #         self.value_gasoline.price_extra,
    #         'values not set'
    #     )

    #     self.assertEqual(
    #         self.config_step_1.name,
    #         config_session_id.config_step_name,
    #         'Names are Equal'
    #     )
    #     productConfigDomainId = self.productConfigDomain.create({
    #         'name': 'Restriction1'
    #     })
    #     self.domainConfigDomainLine = self.env['product.config.domain.line'].create({
    #         'attribute_id': self.attr_color.id,
    #         'condition': 'in',
    #         'value_ids': [(6, 0, [self.value_red.id])],
    #         'operator': 'and',
    #         'domain_id': productConfigDomainId.id,
    #     })
    #     self.productConfigLine = self.env['product.config.line'].create({
    #         'product_tmpl_id': self.config_product.id,
    #         'attribute_id': self.attr_engine.id,
    #         'attribute_line_id': self.env.ref('product_configurator.product_attribute_line_2_series_engine').id,
    #         'value_ids': [(6, 0, [
    #             self.env.ref('product_configurator.product_attribute_value_218i').id,
    #             self.env.ref('product_configurator.product_attribute_value_220i').id,
    #             self.env.ref('product_configurator.product_attribute_value_228i').id,
    #             self.env.ref('product_configurator.product_attribute_value_m235i').id,
    #             self.env.ref('product_configurator.product_attribute_value_m235i_xdrive').id])],
    #         'domain_id': productConfigDomainId.id,
    #     })

    def test_03_get_trans_implied(self):
        self.domain_gasolin.write({'implied_ids': [(6, 0, [self.domain_engine.id])]})
        trans_implied_ids = self.domain_gasolin.trans_implied_ids.ids
        self.assertEqual(
            trans_implied_ids[-1],
            self.domain_engine.id,
            'Error: If value not exists\
            Method: _get_trans_implied()'
        )

    def test_04_check_value_attributes(self):
        with self.assertRaises(ValidationError):
            self.config_product.config_line_ids.write({
                'attribute_line_id': self.attr_engine.id,
                'value_ids': [(6, 0, [self.value_gasoline.id])]
            })

    def test_05_check_config_step(self):
        with self.assertRaises(ValidationError):
            config_step_line = self.env['product.config.step.line'].create({
                'product_tmpl_id': self.config_product.id,
                'config_step_id': self.config_step_engine.id,
                'attribute_line_ids': [(6, 0, [self.attribute_line.id])]
            })

    def test_06_config_session(self):
        # check for _compute_cfg_price
        session_id = self.productConfigSession.create({
            'product_tmpl_id': self.config_product.id,
            'value_ids': [(6, 0, [self.value_gasoline.id, self.value_transmission.id, self.value_red.id])],
            'user_id': self.env.user.id,
        })
        self.assertEqual(
            session_id.price,
            self.config_product.list_price,
            'Error: If different session price and list_price\
            Method: _compute_cfg_price'
        )

        # check for _get_custom_vals_dict
        productConfigSessionCustVals = self.env['product.config.session.custom.value'].create({
            'cfg_session_id': session_id.id,
            'attribute_id': self.attr_fuel.id,
            'value': 'fuel vals'
        })
        checkCharval = session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkCharval.values())[0],
            productConfigSessionCustVals.value,
            'Error: If Not Char value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Int
        self.attr_fuel.custom_type = 'int'
        productConfigSessionCustVals.update({'value': 154})
        checkIntval = session_id._get_custom_vals_dict()

        # _compute_config_step_name
        self.assertEqual(
            list(checkIntval.values())[0],
            literal_eval(productConfigSessionCustVals.value),
            'Error: If Not Integer value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Float
        self.attr_fuel.custom_type = 'float'
        productConfigSessionCustVals.update({'value': 94.5})
        checkFloatval = session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkFloatval.values())[0],
            literal_eval(productConfigSessionCustVals.value),
            'Error: If Not Float value or False\
            Method: _get_custom_vals_dict()'
        )
        # check for custom type Binary
        irAttachement = self.env['ir.attachment'].create({
            'name': 'Test attachement',
        })
        self.attr_color.custom_type = 'binary'
        productConfigSessionCustVals1 = self.env['product.config.session.custom.value'].create({
            'cfg_session_id': session_id.id,
            'attribute_id': self.attr_color.id,
            'attachment_ids': [(6, 0, [irAttachement.id])]
        })
        checkBinaryval = session_id._get_custom_vals_dict()
        self.assertEqual(
            list(checkBinaryval.values())[1],
            productConfigSessionCustVals1.attachment_ids,
            'Error: If Not attachement\
            Method: _get_custom_vals_dict()'
        )
        with self.assertRaises(ValidationError):
            session_id._compute_config_step_name()

        # unlink custom value
        productConfigSessionCustVals.unlink()
        productConfigSessionCustVals1.unlink()

        # configure product
        self._configure_product_nxt_step()
        config_session = self.productConfigSession.search([
            ('product_tmpl_id', '=', self.config_product.id)])
        self.assertTrue(
            config_session.config_step_name,
            'Error: If not config step name\
            Method: _compute_config_step_name()'
        )


        # # check for _compute_cfg_weight
        # config_session._compute_cfg_weight()
        # self.assertEqual(
        #     config_session.weight,`
        #     0.0,
        #     'Error: If not different weight and False\
        #     Method: _compute_cfg_weight()'
        # )
        # self.value_gasoline.price_ids.weight_extra = 34
        # checkWeight1 = config_session._compute_cfg_weight()
        # self.assertEqual(
        #     config_session.weight,
        #     34,
        #     'values not set'
        # )
        #
        # compute_domain
        productConfigDomainId = self.productConfigDomain.create({
            'name': 'Restriction1'
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

        productConfigDomainId.compute_domain()
        self.assertTrue(
           self.domainConfigDomainLine,
           'Exsits'
        )

        # _check_value_ids
        config_session = self.config_session_1.create({
            'product_tmpl_id': self.config_product.id,
            'user_id': self.res_user_id.id,
            'state': 'draft',
        })
        with self.assertRaises(ValidationError):
            self.env['product.config.session'].search_variant()

        # check for search duplicate variant
        variant_id = self.config_product.product_variant_ids
        checkSearchvarient = config_session.search_variant()
        self.assertEqual(
            checkSearchvarient,
            variant_id,
            'Error: If Not Equal Variant or False\
            Method: search_variant()'
        )

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

        # check for check_custom_type
        with self.assertRaises(ValidationError):
            self.env['product.config.session.custom.value'].create({
                'attribute_id':self.value_silver.attribute_id.id,
                'cfg_session_id':config_session.id,
                'value': 'Test',
                'attachment_ids': [(6, 0, [irAttachement.id])],
            })

        self.attr_color.custom_type = 'binary'
        with self.assertRaises(ValidationError):
            self.env['product.config.session.custom.value'].create({
                'attribute_id':self.value_silver.attribute_id.id,
                'cfg_session_id':config_session.id,
                'value': 'Test',
                'attachment_ids': [(6, 0, [irAttachement.id])],
            })

        self.product_tmpl_id.configure_product()
        config_wizard_action = self.productConfWizard.action_next_step()
        product_config_wizard = self.productConfWizard.create({
            'product_tmpl_id':  self.product_tmpl_id.id,
        })
        product_config_wizard.action_next_step()
        product_config_wizard.write({
            '__attribute-{}'.format(self.attribute_1.id): self.attribute_vals_1.id,
            '__attribute-{}'.format(self.attribute_2.id): self.attribute_vals_3.id
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
        productConfigSessionCustVals = self.env['product.config.session.custom.value'].create({
            'cfg_session_id': config_session_1.id,
            'attribute_id': self.attribute_1.id,
            'value': 'Coke'
        })
        config_session_1.create_get_variant()

        total_included = base_prices['total_included']
        total_excluded = base_prices['total_excluded']

        prices = {
            'vals': [
                ('Base', self.config_product.name, total_excluded)
            ],
            'total': total_included,
            'taxes': total_included - total_excluded,
            'currency': currency.name
        }
        # print("-----------------prices------------------",prices)
        component_prices = config_session_id.get_components_prices(
            prices, pricelist, self.config_session_1.value_ids)

        # print("-----------component_prices-------------",component_prices)
        self.assertTrue(prices)


    # def test_06_get_config_image(self):
    #     ProductId = self.config_product.id
    #     print("-------ProductId",ProductId)
    #     ProductImageId = self.config_product.config_image_ids
    #     print("-------ProductImageId",ProductImageId.ids)
    #     ValueIds = self.config_session_1.value_ids.ids
    #     print("-------ValueIds",ValueIds)
    #     aaa = self.value_gasoline.custom_vals
    #     print("------------aaa------------------",aaa)
    #     check = self.config_session_1.get_config_image()
    #     print("--------------check---------------------",check)
    #     self.assertFalse(self.config_session_1.value_ids.ids)
    #     self.assertFalse(self.value_gasoline.custom_vals)

    # def test_07_get_option_values(self):
    #     productConfigDomainId = self.productConfigDomain.create({
    #         'name': 'Restriction1',
    #         })
    #     self.domainConfigDomainLine = self.env['product.config.domain.line'].create({
    #         'attribute_id': self.attr_color.id,
    #         'condition': 'in',
    #         'value_ids': [(6, 0, [self.value_red.id])],
    #         'operator': 'and',
    #         'domain_id': productConfigDomainId.id,
    #     })
    #     config_session_id = self.config_session_1.search([(
    #         'product_tmpl_id', '=', self.config_product.id)])
    #     test1 = self.domainConfigDomainLine.value_ids
    #     pricelist = self.env.user.partner_id.property_product_pricelist
    #     test = self.config_product.with_context({'pricelist': pricelist.id})
    #     component_prices = config_session_id._get_option_values(
    #         pricelist, value_ids)

        # self.assertFalse(self.domainConfigDomainLine.value_ids)


        # test = pricelist.sudo().browse(self.config_session_1.value_ids).filtered(
        #     lambda x: x.product_id.price)
        # print("-----------test-----------------",test)
