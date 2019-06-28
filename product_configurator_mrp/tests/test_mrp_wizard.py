from odoo.addons.product_configurator.tests.\
    test_product_configurator_test_cases import ProductConfiguratorTestCases


class TestMrpWizard(ProductConfiguratorTestCases):

    def setUp(self):
        super(TestMrpWizard, self).setUp()
        self.ProductConfiguratorMrp = self.env['product.configurator.mrp']

    def test_00_action_config_done(self):
        self._configure_product_nxt_step()
        product_config_wiz = self.env['product.configurator'].search(
            [('product_tmpl_id', '=', self.config_product.id)])
        vals = product_config_wiz.action_config_done()
        self.assertEqual(
            vals['res_id'],
            self.config_product.product_variant_ids.id,
            'Not Equal'
        )
