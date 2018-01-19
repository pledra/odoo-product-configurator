# -*- coding: utf-8 -*-

from odoo import models, fields, api

DISPLAY_SELECTION = [('hide', 'Hide'), ('value', 'Value Only'), ('attribute', 'With Label')]


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'
    _order = 'product_tmpl_id, sequence, id'


    sequence = fields.Integer(string='Sequence', default=10)
    display_mode = fields.Selection(DISPLAY_SELECTION, default='value', required=True)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'
    _order = 'sequence, name'
    # test failed because of random order
