# -*- coding: utf-8 -*-

from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None):
        """Add bill of matrials to the configured variant."""
        if custom_values is None:
            custom_values = {}

        variant = super(ProductTemplate, self).create_get_variant(
            value_ids, custom_values=custom_values
        )
        attr_products = variant.attribute_value_ids.mapped('product_id')

        line_vals = [
            (0, 0, {'product_id': product.id}) for product in attr_products
        ]

        values = {
            'product_tmpl_id': self.id,
            'product_id': variant.id,
            'bom_line_ids': line_vals
        }

        self.env['mrp.bom'].create(values)

        return variant
