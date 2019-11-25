from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    def website_product_price_extra_value(self, product_tmpl, pricelist_id):
        template_value_obj = self.env['product.template.attribute.value']
        product_template_value_ids = template_value_obj.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('product_attribute_value_id', 'in', self.ids)]
        )
        extra_prices = {}
        for av in product_template_value_ids:
            product = av.product_attribute_value_id.product_id
            if product:
                extra_prices[av.product_attribute_value_id.id] = product.with_context(
                    pricelist=int(pricelist_id)
                ).price
            else:
                if av.product_attribute_value_id.id in extra_prices:
                    extra_prices[av.product_attribute_value_id.id] += av.price_extra
                else:
                    extra_prices[av.product_attribute_value_id.id] = av.price_extra

        return extra_prices
