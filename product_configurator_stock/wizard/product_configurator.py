from odoo import fields, models


class ProductConfiguratorPicking(models.TransientModel):

    _name = "product.configurator.picking"
    _inherit = "product.configurator"
    _description = "Product Configurator Picking"

    picking_id = fields.Many2one(
        comodel_name="stock.picking", required=True, readonly=True
    )
    stock_move_id = fields.Many2one(comodel_name="stock.move", readonly=True)

    def _get_order_line_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""

        product = self.env["product.product"].browse(product_id)
        product = product.with_context(
            lang=self.env.user.lang
        )
        line_vals = {
            "product_id": product_id,
            "picking_id": self.picking_id.id,
            "name": product.partner_ref,
            "product_uom": product.uom_id.id,
            "product_uom_qty": 1,
            "config_session_id": self.config_session_id.id,
        }
        if self.picking_id.location_id and self.picking_id.location_dest_id:
            line_vals.update(
                {
                    "location_id": self.picking_id.location_id.id,
                    "location_dest_id": self.picking_id.location_id.id,
                }
            )
        return line_vals

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorPicking, self).action_config_done()
        if res["res_model"] == self._name:
            return res

        line_vals = self._get_order_line_vals(res["res_id"])
        order_line_obj = self.env["stock.move"]
        specs = order_line_obj._onchange_spec()
        updates = order_line_obj.onchange(line_vals, ["product_id"], specs)
        values = updates.get("value", {})
        for name, val in values.items():
            if isinstance(val, tuple):
                values[name] = val[0]

        values.update(line_vals)
        if self.stock_move_id:
            self.stock_move_id.write(values)
            move_line = self.stock_move_id
        else:
            move_line = self.picking_id.move_lines.create(values)
        return
