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
