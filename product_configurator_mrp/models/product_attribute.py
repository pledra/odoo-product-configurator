from odoo import api, fields, models


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    quantity = fields.Boolean(
        string='Quantity',
        help='Allow quantity selection in product configuration '
        'for the related product'
    )

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            self.quantity = False
