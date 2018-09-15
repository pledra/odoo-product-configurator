from odoo.tests.common import TransactionCase


class PurchaseConfigurProduct(TransactionCase):

    def setUp(self):
        super(PurchaseConfigurProduct, self).setUp()
        self.config_product = self.env.ref('product_configurator.bmw_2_series')

        self.PurchaseOrder = self.env['purchase.order']
        self.partner_id = self.env.ref('base.res_partner_1')
        self.ProductConfWizard = self.env['product.configurator.purchase']

        self.field_fuel = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_fuel').id)
        self.field_engine = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_engine').id)
        self.field_line = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_model_line').id)
        self.field_color = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_color').id)
        self.field_rims = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_rims').id)
        self.field_tapistry = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_tapistry').id)
        self.field_transmission = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_transmission').id)
        self.field_options = '__attribute-{}'.format(self.env.ref(
            'product_configurator.product_attribute_options').id)

    def test_purchase_product_configuration(self):
        """Test product configuration from purchase order"""

        purchase_order = self.PurchaseOrder.create({
            'partner_id': self.partner_id.id,
        })
        product_config_wizard = self.ProductConfWizard.create({
            'product_tmpl_id': self.config_product.id,
            'order_id': purchase_order.id
        })

        val_fuel = self.env.ref(
            'product_configurator.product_attribute_value_gasoline')
        val_engine = self.env.ref(
            'product_configurator.product_attribute_value_218i')
        val_line = self.env.ref(
            'product_configurator.product_attribute_value_silver')
        val_color = self.env.ref(
            'product_configurator.product_attribute_value_rims_387')
        val_rims = self.env.ref(
            'product_configurator.product_attribute_value_luxury_line')
        val_tapistry = self.env.ref(
            'product_configurator.product_attribute_value_tapistry' +
            '_oyster_black')
        val_transmission = self.env.ref(
            'product_configurator.product_attribute_value_steptronic')
        val_options_1 = self.env.ref(
            'product_configurator.product_attribute_value_smoker_package')
        val_options_2 = self.env.ref(
            'product_configurator.product_attribute_value_sunroof')
        product_config_wizard.write({
            self.field_fuel: val_fuel.id,
            self.field_engine: val_engine.id,
            self.field_line: val_line.id,
            self.field_color: val_color.id,
            self.field_rims: val_rims.id,
            self.field_tapistry: val_tapistry.id,
            self.field_transmission: val_transmission.id,
            self.field_options: [[6, 0, [val_options_1.id, val_options_2.id]]],
        })
        product_config_wizard.action_config_done()
