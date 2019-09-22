from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    def get_attr_value_name(self, product_tmpl, pricelist_id):
        self = self.with_context({
            'show_price_extra': False,
            'active_id': product_tmpl.id,
            'show_attribute': False,
        })
        res = self.name_get()
        extra_prices = {
            av.id: av.price_extra for av in self if av.price_extra
        }

        res_prices = []
        pricelist = self.env['product.pricelist'].browse(int(pricelist_id))
        price_precision = pricelist.currency_id.decimal_places or 2

        for val in res:
            price_extra = extra_prices.get(val[0])
            if price_extra:
                val = (
                    val[0], '%s ( +%s )' %
                    (val[1], ('{0:,.%sf}' % (
                        price_precision
                    )).format(price_extra))
                )
            res_prices.append(val)
        return res_prices
