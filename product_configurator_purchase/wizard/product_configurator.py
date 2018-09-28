from odoo import api, fields, models


class ProductConfiguratorPurchase(models.TransientModel):

    _name = 'product.configurator.purchase'
    _inherit = 'product.configurator'

    order_id = fields.Many2one(
        comodel_name='purchase.order',
        required=True,
        readonly=True,
    )
    order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        readonly=True
    )

    def _get_order_line_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""
        product = self.env['product.product'].browse(product_id)

        return {
            'product_id': product_id,
            'product_qty': 1,
            'name': product._get_mako_tmpl_name(),
            'product_uom': product.uom_id.id,
            'price_unit': 1,
            'date_planned': fields.Datetime.now(),
        }

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorPurchase, self).action_config_done()

        line_vals = self._get_order_line_vals(res['res_id'])

        if self.order_line_id:
            self.order_line_id.write(line_vals)
        else:
            self.order_id.write({'order_line': [(0, 0, line_vals)]})

        return
