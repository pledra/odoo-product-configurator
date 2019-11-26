from odoo import models, api


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def website_product_price_extra_value(self, product_tmpl, pricelist):
        template_value_obj = self.env['product.template.attribute.value']
        attr_value_ids = product_tmpl.attribute_line_ids.mapped('value_ids')
        pt_attr_value_ids = template_value_obj.search([
            ('product_tmpl_id', '=', product_tmpl.id),
            ('product_attribute_value_id', 'in', attr_value_ids.ids)]
        )
        extra_prices = self.get_attribute_value_extra_prices(
            pt_attr_value_ids=pt_attr_value_ids, pricelist=pricelist
        )
        return extra_prices
