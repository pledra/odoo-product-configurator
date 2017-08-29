# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAttributeValueLine(models.Model):
    _name = 'product.attribute.value.line'

    related_attribute_id = fields.Many2one(
        related='attribute_line_id.attribute_id', string='Product Attribute')
    attribute_line_id = fields.Many2one('product.attribute.line',
                                        'Product Attribute')
    attrib_value_id = fields.Many2one('product.attribute.value',
                                      'Attribute Value')
    is_default = fields.Boolean("Is Default")

    @api.onchange('is_default')
    def onchange_values(self):
        if self.is_default:
            # Check if its checked earlier or not
            if not self._origin.attribute_line_id.default_val:
                self._origin.attribute_line_id.write(
                    {'default_val': self._origin.attrib_value_id.id})
            else:
                title = (
                        "Warning for Attribute %s") % self._origin.attribute_line_id.attribute_id.name
                message = (
                          "Attribute Value %s is already set!") % self._origin.attribute_line_id.default_val.name
                warning = {
                    'title': title,
                    'message': message,
                }
                self.update({'is_default': False})
                return {'warning': warning}
        else:
            # Check if its checked earlier or not
            if self._origin.attribute_line_id.default_val:
                self._origin.attribute_line_id.write({'default_val': False})
