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
        variant.configurator_create_bom()
        return variant

    @api.multi
    def configurator_default_bom(self):
        """
        :returns default dictionary bom to use as a default bom
        to include in every configuration

        Handy for overwriting.
        """
        return {
            'product_tmpl_id': self.id,
            'bom_line_ids': [],
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def configurator_default_bom_variant(self):
        result = self.product_tmpl_id.configurator_default_bom()
        result['product_id'] = self.id
        return result

    @api.multi
    def configurator_create_bom(self):
        """Routine to create a bom.

        By default, this assumes that if there is a bom for the variant,
        then don't try and create another!
        """
        Mrp_bom = self.env['mrp.bom']

        for variant in self:
            if Mrp_bom.search([('product_id', '=', variant.id)]):
                continue

            values = variant.configurator_default_bom_variant()
            line_vals = values['bom_line_ids']
            # loop, don't use mapped, as the product may be mapped by multiple
            # attributes
            for attr_value in variant.attribute_value_ids:
                bom_line_vals = attr_value.bom_line_dictionary()
                if bom_line_vals:
                    line_vals.append([(0, 0, bom_line_vals)])

            Mrp_bom.create(values)


class ProductAttributeValues(models.Model):
    _inherit = "product.attribute.value"

    @api.multi
    def bom_line_dictionary(self):
        result = {}
        if self.product_id:
            result.update(
                {'product_id': self.product_id.id}
            )
        return result
