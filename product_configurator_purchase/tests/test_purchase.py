from odoo.addons.product_configurator.tests.\
    test_product_configurator_test_cases import ProductConfiguratorTestCases
from datetime import datetime


class Purchase(ProductConfiguratorTestCases):
    def setUp(self):
        super(Purchase, self).setUp()
        self.purchaseOrder = self.env['purchase.order']
        self.purchaseOrderLine = self.env['purchase.order.line']
        self.resPartner = self.env.ref(
            'product_configurator_purchase.partenr1')
        self.currency_id = self.env.ref('base.USD')
        self.company_id = self.env.ref('base.main_company')
        self.ProductTemplate = self.env.ref(
            'product_configurator.bmw_2_series')
        self.ProductConfWizard = self.env['product.configurator.purchase']

    def test_00_action_config_start(self):
        purchase_order_id = self.purchaseOrder.create({
            'partner_id': self.resPartner.id,
            'currency_id': self.currency_id.id,
            'date_order': datetime.now(),
            'date_planned': datetime.now(),
            'company_id': self.company_id.id,
        })
        context = dict(
            default_order_id=purchase_order_id.id,
            wizard_model='product.configurator.purchase',
        )
        self.ProductConfWizard = self.env['product.configurator.purchase'].\
            with_context(context)
        purchase_order_id.action_config_start()
        self._configure_product_nxt_step()
        purchase_order_id.order_line.reconfigure_product()
        product_tmpl = purchase_order_id.order_line.product_id.product_tmpl_id
        self.assertEqual(
            product_tmpl.id,
            self.config_product.id,
            'Error: If product_tmpl not exsits\
            Method: action_config_start()'
        )
