from odoo import models


class ProductConfiguratorSale(models.TransientModel):

    _inherit = 'product.configurator.sale'

    def _get_order_line_vals(self, product_id):
        """Add the config session related bom_id to the sale order line"""
        vals = super(ProductConfiguratorSale, self)._get_order_line_vals(
            product_id=product_id
        )
        vals.update(bom_id=self.bom_id.id)
        return vals
