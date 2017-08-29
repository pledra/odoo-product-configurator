# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'
    
    @api.multi
    def _get_attribute_values(self):
        for line in self:
            attribute_value_ids = []
            for new_value in line.value_idss:
                attrib_value_id = new_value.attrib_value_id and new_value.attrib_value_id.id or False
                if attrib_value_id:
                    attribute_value_ids.append(attrib_value_id)
            line.value_ids = [(6,0,attribute_value_ids)]

    value_idss = fields.One2many('product.attribute.value.line', 'attribute_line_id', 'Values', copy=True)
    value_ids = fields.Many2many(compute='_get_attribute_values', comodel_name='product.attribute.value', string='Attribute Values')
