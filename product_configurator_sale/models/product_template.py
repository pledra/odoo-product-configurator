from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1,
                              pricelist=False, parent_combination=False,
                              only_template=False):
        result_dict = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            pricelist=pricelist, parent_combination=parent_combination,
            only_template=only_template)
        product = self.env['product.product'].browse(product_id)
        if product and product.value_custom_ids:
            result_dict['product_id'] = product.id
            result_dict['display_name'] = product.name_get()[0][1]
            result_dict['price'] = product.price if pricelist else \
                product.price_compute('list_price')[product.id]
        return result_dict
