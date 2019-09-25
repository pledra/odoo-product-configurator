from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    def get_attr_value_name(self, product_tmpl, pricelist_id):
        self = self.with_context({
            'show_price_extra': False,
            'active_id': product_tmpl.id,
            'show_attribute': False,
        })

        res =  self.name_get()
        product_template_id = self.env.context.get('active_id', False)
        template_value_obj = self.env['product.template.attribute.value']
        res_prices = []
        pricelist = self.env['product.pricelist'].browse(int(pricelist_id))
        price_precision = pricelist.currency_id.decimal_places or 2
        product_template_value_ids = template_value_obj.search([
            ('product_tmpl_id', '=', product_template_id),
            ('product_attribute_value_id', 'in', self.ids),
            ('price_extra', '!=', 0)]
        )
        extra_prices = {
            av.product_attribute_value_id.id: av.price_extra
            for av in product_template_value_ids
        }
        for val in res:
            price_extra = extra_prices.get(val[0])
            if price_extra:
                val = (val[0], '%s ( +%s )' % (val[1], ('{0:,.%sf}' % (
                    price_precision)).format(price_extra)))
            res_prices.append(val)
        return res_prices
