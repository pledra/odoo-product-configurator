from odoo.addons.product_configurator.tests.\
    product_configurator_test_cases import ProductConfiguratorTestCases
from odoo.tests.common import TransactionCase
from datetime import datetime


class Stock(ProductConfiguratorTestCases):
    def setUp(self):
        super(Stock, self).setUp()
        self.StockPickingType = self.env['stock.picking.type']
        self.stockPicking = self.env['stock.picking']
        # self.stockPicking = self.env['stock.move']
        # self.ProductTemplate = self.env.ref('product_configurator.product_attribute_line_2_series_fuel')
        # self.ProductConfWizard = self.env['product.configurator.picking']
        self.stockLocation = self.env.ref('stock.stock_location_locations')
        self.stockLocation2 = self.env.ref('stock.stock_location_locations_partner')
        self.sequence_id = self.env.ref('stock.sequence_mrp_op')
        self.resPartner = self.env.ref('product_configurator_purchase.partenr1')

    def test_00_action_config_start(self):

        stock_picking_type_id = self.StockPickingType.create({
            'name': 'Test Picking Type',
            'code': 'incoming',
            'sequence_id': self.sequence_id.id,
            'allow_configuration': True,
        })
        stockPickingId = self.stockPicking.create({
            'partner_id': self.resPartner.id,
            'picking_type_id': stock_picking_type_id.id,
            'location_id': self.stockLocation.id,
            'location_dest_id': self.stockLocation2.id,
            
        })
        # product_config_wizard = self.ProductConfWizard.create({
        #     'product_tmpl_id': self.ProductTemplate.id,
        # })
        
        context = dict(
                default_picking_id=stockPickingId.id,
                wizard_model='product.configurator.picking',
        )
        # ProductTemplate = self.ProductTemplate.create({
        #     'name': self.ProductTemplate,
        #     'product_tmpl_id': self.ProductTemplate.id,
        # })

        self.ProductConfWizard = self.env['product.configurator.picking'].with_context(context)
        action = stockPickingId.action_config_start()
        print("-----------action----------------------",action)
        self.productConfigure = self._configure_product_nxt_step()
        reconfig_action = stockPickingId.move_lines.reconfigure_product()
        reconfig_action.get('res_id')
        self.assertTrue(
            stockPickingId.id,
            'picking id not exsits'
        )
        self.assertTrue(
            stockPickingId.move_lines.id,
            'move id not exsits'
        )
        self.assertTrue(
            stockPickingId.move_lines.product_id,
            'product id not exsits'
        )