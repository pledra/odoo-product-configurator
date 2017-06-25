# -*- coding: utf-8 -*-

from openerp import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None):
        """Add the name generated from the mako template to sales description
        to have the value transfered to the order lines"""
        variant = super(ProductTemplate, self).create_get_variant(
            value_ids=value_ids, custom_values=custom_values)
        if self.mako_tmpl_name:
            variant.write({
                'description_sale': variant._get_mako_tmpl_name()
            })
        return variant

    # TODO: Refactor so we can add the value before variant creation
