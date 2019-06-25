from odoo import api, models
from odoo.tools import pycompat
from odoo.tools import float_compare


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _website_price(self):
        """Set website_price of configurable product
        Uses formula ::
        website_price = list_price + sum(extra price of default attr values)"""
        config_products = self.filtered('config_ok')
        super(ProductTemplate, self - config_products)._website_price()
        for template in config_products:
            result = template._get_website_price()
            price_dict = result.get(template.id, {})
            template.website_price =\
                price_dict.get('website_price', template.list_price)
            template.website_public_price =\
                price_dict.get('website_public_price', template.list_price)
            template.website_price_difference =\
                price_dict.get('website_price_difference', 0.0)

    @api.multi
    def _get_website_price(self):
        result = {}
        qty = self._context.get('quantity', 1.0)
        partner = self.env.user.partner_id
        current_website = self.env['website'].get_current_website()
        pricelist = current_website.get_current_pricelist()
        company_id = current_website.company_id

        context = dict(self._context, pricelist=pricelist.id, partner=partner)
        self2 = (
            self.with_context(context)
            if self._context != context else self
        )
        ret = self.env.user.has_group(
            'sale.group_show_price_subtotal'
        ) and 'total_excluded' or 'total_included'

        for p, p2 in pycompat.izip(self, self2):
            taxes_ids = p.sudo().taxes_id.filtered(
                lambda x: x.company_id == company_id)
            taxes = partner.property_account_position_id.map_tax(taxes_ids)
            website_price = taxes.compute_all(
                p2.price,
                pricelist.currency_id,
                quantity=qty,
                product=p2,
                partner=partner
            )[ret]

            price_without_pricelist = p.list_price
            if company_id.currency_id != pricelist.currency_id:
                price_without_pricelist = company_id.currency_id.compute(
                    price_without_pricelist, pricelist.currency_id)
            price_without_pricelist = taxes.compute_all(
                price_without_pricelist, pricelist.currency_id)[ret]
            website_price_difference = True if float_compare(
                price_without_pricelist,
                website_price,
                precision_rounding=pricelist.currency_id.rounding
            ) > 0 else False
            website_public_price = taxes.compute_all(
                p2.lst_price, quantity=qty, product=p2, partner=partner)[ret]
            result.update({
                p.id: {
                    'website_price': website_price,
                    'website_price_difference': website_price_difference,
                    'website_public_price': website_public_price,
                }
            })
        return result
