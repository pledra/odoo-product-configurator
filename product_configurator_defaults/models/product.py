# -*- coding: utf-8 -*-

from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def get_variant_vals(self, value_ids, custom_values=None, **kwargs):
        """ Add default values for attribute lines"""
        self.ensure_one()

        # Add default values
        value_ids = self.env['product.attribute.value'].browse(value_ids)
        default_lines = self.attribute_line_ids.filtered('default')
        for d in default_lines:
            if d.default.attribute_id not in value_ids.mapped('attribute_id'):
                if not d.custom or (
                    d.custom and
                    d.default.attribute_id.id not in custom_values.keys()
                ):
                    value_ids += d.default

        return super(ProductTemplate, self).get_variant_vals(
            value_ids.ids, custom_values, **kwargs)
