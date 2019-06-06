from odoo.addons.product_configurator.tests. \
    product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.tests.common import TransactionCase
from datetime import datetime


class SaleOrder(TransactionCase):

    def setUp(self):
        super(SaleOrder, self).setUp()
        self.SaleOrderId = self.env.ref('sale.sale_order_1')
        self.SaleOrderLineId = self.env.ref('sale.sale_order_line_1')
        self.ProductId = self.env.ref('product_configurator.product_bmw_sport_line')
        self.ProductAttributeFuel = self.env.ref(
            'product_configurator.product_attribute_fuel')
        self.ProductAttributeValueGasoline = self.env.ref(
            'product_configurator.product_attribute_value_gasoline')
        self.ProductAttributeValueFuel = \
            self.ProductAttributeValueGasoline.attribute_id.id
        self.resPartner = self.env.ref('product_configurator_purchase.partenr1')
        self.currency_id = self.env.ref('base.USD')
        self.company_id = self.env.ref('base.main_company')
        self.ProductTemplate = self.env.ref('product_configurator.bmw_2_series')

    def test_00_reconfigure_product(self):
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        self.SaleOrderId = self.SaleOrderId
        # test_product = self.env['product.product'].create({
        #     'name': 'Test Product Configuration',
        #     'config_ok': True,
        # })
        # self.SaleOrderLineId.reconfigure_product()

class Purchase(ProductConfiguratorTestCases):

    def test_00_action_config_start(self):
        # self.ProductId = self.ProductId.create({
        #     'config_ok': True,
        #     'name': 'Product Configurator',
        #     'product_tmpl_id': self.ProductTemplate.id,
        # })
        # print("self.Product----------------------------------------!", self.ProductId)
        print("###############",purchase_order_id.id)
        purchase_order_id.action_config_start()
        self.configure_product = self._configure_product_nxt_step()
        print("\n\n\n --------purchase_order_id", purchase_order_id.order_line)
        self.config_product.product_variant_ids.reconfigure_product()
        action = self.config_product.product_variant_ids.reconfigure_product()
        res_id = action.get('res_id')
        print("action ================", action, res_id) 

        self.assertTrue(
            purchase_order_id.id,
            'order id not exsits'
        )

        self.assertTrue(
            purchase_order_line_id.id,
            'order line id not exsits'
        )






        # self.purchaseOrderLine.purchase_order_id.reconfigure_product()
