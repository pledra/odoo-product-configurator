from odoo import fields, models


class ProductConfiguratorSale(models.TransientModel):

    _name = "product.configurator.sale"
    _inherit = "product.configurator"
    _description = "Product Configurator Sale"

    order_id = fields.Many2one(
        comodel_name="sale.order", required=True, readonly=True
    )
    order_line_id = fields.Many2one(
        comodel_name="sale.order.line", readonly=True
    )

    def _get_order_line_vals(self, product_id):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""
        product = self.env["product.product"].browse(product_id)
        line_vals = {"product_id": product_id, "order_id": self.order_id.id}
        extra_vals = self.order_line_id._prepare_add_missing_fields(line_vals)
        line_vals.update(extra_vals)
        line_vals.update(
            {
                "config_session_id": self.config_session_id.id,
                "price_unit": self.config_session_id.price,
                "name": product._get_mako_tmpl_name(),
            }
        )
        return line_vals

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super(ProductConfiguratorSale, self).action_config_done()
        if res.get("res_model") == self._name:
            return res
        model_name = "sale.order.line"
        line_vals = self._get_order_line_vals(res["res_id"])

        # Call onchange explicite as write and create
        # will not trigger onchange automatically
        order_line_obj = self.env[model_name]
        cfg_session = self.config_session_id
        specs = cfg_session.get_onchange_specifications(model=model_name)
        updates = order_line_obj.onchange(line_vals, ["product_id"], specs)
        values = updates.get("value", {})
        values = cfg_session.get_vals_to_write(values=values, model=model_name)
        values.update(line_vals)

        if self.order_line_id:
            self.order_line_id.write(values)
        else:
            self.order_id.write({"order_line": [(0, 0, values)]})
        return
