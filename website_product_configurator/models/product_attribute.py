from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    def get_attr_value_name(self, product_tmpl, pricelist_id):
        template_value_obj = self.env['product.template.attribute.value']
        pricelist = self.env['product.pricelist'].browse(int(pricelist_id))
        product_template_value_ids = template_value_obj.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('product_attribute_value_id', 'in', self.ids)]
        )
        extra_prices = {}
        for av in product_template_value_ids:
            product = av.product_attribute_value_id.product_id
            if product:
                extra_prices[av.product_attribute_value_id.id] = product.with_context(
                    pricelist=pricelist.id
                ).price
            else:
                extra_prices[av.product_attribute_value_id.id] = av.price_extra

        return extra_prices
