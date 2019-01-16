from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductAttributePrice(models.Model):
    _inherit = "product.attribute.price"
    # Leverage product.attribute.price to compute the extra weight each
    # attribute adds

    weight_extra = fields.Float(
        string="Weight",
        digits=dp.get_precision('Product Weight')
    )


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    weight_extra = fields.Float(
        string='Attribute Weight Extra',
        compute='_compute_weight_extra',
        inverse='_set_weight_extra',
        default=0.0,
        digits=dp.get_precision('Product Weight'),
        help="Weight Extra: Extra weight for the variant with this attribute"
        "value on sale price. eg. 200 price extra, 1000 + 200 = 1200."
    )

    @api.one
    def _compute_weight_extra(self):
        product_tmpl_id = self._context.get('active_id')
        if product_tmpl_id:
            price = self.price_ids.filtered(
                lambda price: price.product_tmpl_id.id == product_tmpl_id
            )
            self.weight_extra = price.weight_extra
        else:
            self.weight_extra = 0.0

    def _set_weight_extra(self):
        product_tmpl_id = self._context.get('active_id')
        if not product_tmpl_id:
            return

        AttributePrice = self.env['product.attribute.price']
        prices = AttributePrice.search([
            ('value_id', 'in', self.ids),
            ('product_tmpl_id', '=', product_tmpl_id)
        ])
        updated = prices.mapped('value_id')
        if prices:
            prices.write({'weight_extra': self.weight_extra})
        else:
            for value in self - updated:
                AttributePrice.create({
                    'product_tmpl_id': product_tmpl_id,
                    'value_id': value.id,
                    'weight_extra': self.weight_extra,
                })
