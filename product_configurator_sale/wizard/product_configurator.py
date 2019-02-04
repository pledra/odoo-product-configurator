from odoo import api, fields, models


class ProductConfiguratorSale(models.TransientModel):

    _name = 'product.configurator.sale'
    _inherit = 'product.configurator'

    order_id = fields.Many2one(
        comodel_name='sale.order',
        required=True,
        readonly=True
    )
    order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        readonly=True
    )

    def _get_order_line_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""

        line_vals = {
            'product_id': product_id,
            'order_id': self.order_id.id
        }

        extra_vals = self.order_line_id._prepare_add_missing_fields(line_vals)
        line_vals.update(extra_vals)
        return line_vals

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorSale, self).action_config_done()

        line_vals = self._get_order_line_vals(res['res_id'])

        if self.order_line_id:
            self.order_line_id.write(line_vals)
        else:
            self.order_id.write({'order_line': [(0, 0, line_vals)]})

        return
