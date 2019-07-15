from odoo.addons.product_configurator.tests.\
    test_product_configurator_test_cases import ProductConfiguratorTestCases


class Stock(ProductConfiguratorTestCases):
    def setUp(self):
        super(Stock, self).setUp()
        self.StockPickingType = self.env['stock.picking.type']
        self.stockPicking = self.env['stock.picking']
        self.stockLocation = self.env.ref(
            'stock.stock_location_locations')
        self.stockLocation2 = self.env.ref(
            'stock.stock_location_locations_partner')
        self.sequence_id = self.env.ref(
            'stock.sequence_mrp_op')
        self.resPartner = self.env.ref(
            'stock.res_company_1')

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
        context = dict(
            default_picking_id=stockPickingId.id,
            wizard_model='product.configurator.picking',
        )
        self.ProductConfWizard = self.env['product.configurator.picking'].\
            with_context(context)
        stockPickingId.action_config_start()
        self._configure_product_nxt_step()
        stockPickingId.move_lines.reconfigure_product()
        product_tmpl = stockPickingId.move_lines.product_id.product_tmpl_id
        self.assertEqual(
            product_tmpl.id,
            self.config_product.id,
            'Error: If product_tmpl not exsits\
            Method: action_config_start()'
        )
