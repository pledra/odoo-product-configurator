from odoo.addons.product_configurator.tests.\
    test_product_configurator_test_cases import \
    ProductConfiguratorTestCases
from datetime import datetime


class TestMrp(ProductConfiguratorTestCases):

    def setUp(self):
        super(TestMrp, self).setUp()
        self.mrpBomConfigSet = self.env['mrp.bom.line.configuration.set']
        self.mrpBomConfig = self.env['mrp.bom.line.configuration']
        self.mrpBom = self.env['mrp.bom']
        self.mrpBomLine = self.env['mrp.bom.line']
        self.productProduct = self.env['product.product']
        self.productTemplate = self.env['product.template']
        self.mrpProduction = self.env['mrp.production']
        self.product_id = self.env.ref('product.product_product_3')

        # create bom
        self.bom_id = self.mrpBom.create({
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_qty': 1.00,
            'type': 'normal',
            'ready_to_produce': 'all_available',
        })
        # create bom line
        self.bom_line_id = self.mrpBomLine.create({
            'bom_id': self.bom_id.id,
            'product_id': self.product_id.id,
            'product_qty': 1.00,
        })

    def test_00_skip_bom_line(self):
        checkVal = self.mrpBomLine._skip_bom_line(
            product=self.product_id)
        self.assertFalse(
            checkVal,
            'Error: If value exists\
            Method: _skip_bom_line()'
        )
        self.bom_line_id.bom_id.config_ok = True
        self.mrp_config_step = self.mrpBomConfigSet.create({
            'name': 'TestConfigSet',
        })
        self.bom_line_id.write({
            'config_set_id': self.mrp_config_step.id
        })
        # create bom_line_config
        self.mrp_bom_config = self.mrpBomConfig.create({
            'config_set_id': self.mrp_config_step.id,
            'value_ids': [(6, 0, [
                self.value_gasoline.id,
                self.value_218i.id,
                self.value_220i.id,
                self.value_red.id
            ])]
        })
        self.product_id.write({
            'attribute_value_ids': [(6, 0, self.mrp_bom_config.value_ids.ids)]
        })
        self.mrpProduction.create({
            'product_id': self.product_id.id,
            'product_qty': 1.00,
            'product_uom_id': 1.00,
            'bom_id': self.bom_id.id,
            'date_planned_start': datetime.now()
        })
        self.mrpBomLine._skip_bom_line(
            product=self.product_id)
        self.assertFalse(
            checkVal,
            'Error: If value exists\
            Method: _skip_bom_line()'
        )

    def test_01_action_config_start(self):
        mrpProduction = self.mrpProduction.create({
            'product_id': self.product_id.id,
            'product_qty': 1.00,
            'product_uom_id': 1.00,
            'bom_id': self.bom_id.id,
            'date_planned_start': datetime.now()
        })
        context = dict(
            self.env.context,
            default_order_id=mrpProduction.id,
            wizard_model='product.configurator.mrp',
        )
        mrpProduction.action_config_start()
        self.ProductConfWizard = self.env[
            'product.configurator.mrp'].with_context(context)
        self._configure_product_nxt_step()
