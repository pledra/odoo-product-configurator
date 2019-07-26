from odoo import api, fields, models


class ProductConfiguratorPicking(models.TransientModel):

    _name = 'product.configurator.picking'
    _inherit = 'product.configurator'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        required=True,
        readonly=True
    )
    stock_move_id = fields.Many2one(
        comodel_name='stock.move',
        readonly=True
    )

    def _get_order_line_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""

        product = self.env['product.product'].browse(product_id)

        line_vals = {
            'product_id': product_id,
            'picking_id': self.picking_id.id,
            'name': product.partner_ref,
            'product_uom': product.uom_id.id,
        }
        if self.picking_id.location_id and self.picking_id.location_dest_id:
            line_vals.update({
                'location_id': self.picking_id.location_id.id,
                'location_dest_id': self.picking_id.location_id.id,
            })

        return line_vals

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorPicking, self).action_config_done()
        if res['res_model'] == self._name:
            return res

        line_vals = self._get_order_line_vals(res['res_id'])

        if self.stock_move_id:
            self.stock_move_id.write(line_vals)
        else:
            self.picking_id.write({'move_lines': [(0, 0, line_vals)]})

        return
