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
        if res['res_model'] == self._name:
            return res

        line_vals = self._get_order_line_vals(res['res_id'])

        # To call onchange explicite as write and create
        # will not trigger onchange automatically
        order_line_obj = self.env['sale.order.line']
        specs = order_line_obj._onchange_spec()
        updates = order_line_obj.onchange(line_vals, ['product_id'], specs)
        values = updates.get('value', {})
        for name, val in values.items():
            if isinstance(val, tuple):
                values[name] = val[0]
        line_vals.update(values)

        if self.order_line_id:
            self.order_line_id.write(line_vals)
        else:
            self.order_id.write({'order_line': [(0, 0, line_vals)]})

        return
