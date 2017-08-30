# -*- coding: utf-8 -*-
# Copyright (C) 2012 - TODAY, Ursa Information Systems
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'

    @api.multi
    def _get_attribute_values(self):
        for line in self:
            attribute_value_ids = line.value_idss.mapped('attrib_value_id')
            if attribute_value_ids:
                line.value_ids = [(6, 0, attribute_value_ids.ids)]

    value_idss = fields.One2many('product.attribute.value.line',
                                 'attribute_line_id', 'Values', copy=True)
    value_ids = fields.Many2many(compute='_get_attribute_values',
                                 comodel_name='product.attribute.value',
                                 string='Attribute Values')
    default_val = fields.Many2one('product.attribute.value',
                                  compute='_is_default_value',
                                  string="Default Value", store=True)

    @api.depends('value_idss.is_default')
    def _is_default_value(self):
        default_lines = [default for default in
                         self.value_idss.mapped('is_default') if default]
        if default_lines:
            if len(default_lines) == 1:
                for value in self.value_idss:
                    if value.is_default:
                        self.default_val = value.attrib_value_id
            else:
                raise ValidationError(_(
                    "Please select one, first selected option will be valid!"))
        else:
            self.default_val = False
            
    @api.multi
    @api.constrains('value_ids', 'default_val')
    def _check_default_values(self):
        return True
