# -*- coding: utf-8 -*-

from openerp import models, fields, api


class ProductConfiguratorPurchase(models.TransientModel):

    _name = 'product.configurator.purchase'
    _inherit = 'product.configurator'

    order_id = fields.Many2one(
        comodel_name='purchase.order',
        required=True
    )
    order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        readonly=True
    )

    def _extra_line_values(self, product):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""
        return {'name': product._get_mako_tmpl_name()}

    @api.multi
    def action_config_done(self):
        """Add new order line or edit linked order line with new variant"""
        custom_vals = self.config_session_id._get_custom_vals_dict()
        variant = self.product_tmpl_id.create_get_variant(
            self.value_ids.ids, custom_vals)

        order_line_obj = self.env['purchase.order.line']

        vals = {
            'order_id': self.order_id.id,
            'product_id': variant.id,
        }

        if self.order_line_id:
            # TODO: Run onchanges sequentially until no more values are changed
            specs = order_line_obj._onchange_spec()
            line_vals = self.order_line_id.read()[0]
            onchange_updates = order_line_obj.onchange(
                line_vals, ['product_id'], specs)
            onchange_vals = onchange_updates.get('value', {})
            for name, val in onchange_vals.iteritems():
                if isinstance(val, tuple):
                    onchange_vals[name] = val[0]
            vals.update(onchange_vals)
            vals.update(self._extra_line_values(variant))
            self.order_line_id.write(vals)
            return

        # Create cache object and run onchange method to update values
        order_line = order_line_obj.new(vals)
        order_line.onchange_product_id()

        line_vals = {}
        for field, model in order_line._fields.iteritems():
            line_vals[field] = model.convert_to_write(order_line[field])

        line_vals.update(self._extra_line_values(variant))
        order_line_obj.create(line_vals)

        return
