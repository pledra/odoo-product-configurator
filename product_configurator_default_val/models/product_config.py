# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    @api.model
    def create(self, vals):
        product_tmpl = self.env['product.template'].browse(
            vals.get('product_tmpl_id')).exists()
        if product_tmpl:
            default_val_ids = product_tmpl.attribute_line_ids.filtered(
                lambda l: l.default_val).mapped('default_val').ids
            value_ids = vals.get('value_ids')
            if value_ids:
                default_val_ids += value_ids[0][2]
            valid_conf = product_tmpl.validate_configuration(
                default_val_ids, final=False)
            # TODO: Remove if cond when PR with raise error on github is merged
            if not valid_conf:
                raise ValidationError(
                    _('Default values provided generate an invalid '
                      'configuration')
                )
            vals.update({'value_ids': [(6, 0, default_val_ids)]})
        return super(ProductConfigSession, self).create(vals)
