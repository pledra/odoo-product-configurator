# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    @api.constrains('attribute_line_ids')
    def _check_default_values(self):
        """Validate default values set on the product template"""
        default_val_ids = self.attribute_line_ids.filtered(
            lambda l: l.default_val).mapped('default_val').ids

        # TODO: Remove if cond when PR with raise error on github is merged
        if not self.validate_configuration(default_val_ids, final=False):
            raise ValidationError(
                _('Default values provided generate an invalid configuration')
            )

    @api.multi
    @api.constrains('config_line_ids')
    def _check_default_value_domains(self):
        try:
            self._check_default_values()
        except ValidationError:
            raise ValidationError(
                _('Restrictions added make the current default values '
                  'generate an invalid configuration')
            )
