# -*- coding: utf-8 -*-

from odoo import models, fields, api

DISPLAY_SELECTION = [('hide', 'Hide'), ('value', 'Only Value'), ('attribute', 'With Label')]


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'
    _order = 'product_tmpl_id, sequence, id'


    sequence = fields.Integer(string='Sequence', default=10)
    display_mode = fields.Selection(DISPLAY_SELECTION, default='value', required=True)

    def display_format(self):
        result = []
        for record in self:
            if record.display_mode == 'value':
                result.append(u'{%s}' % record.attribute_id.name)
            elif record.display_mode == 'attribute':
                result.append(u'%s: {%s}' % (record.attribute_id.name, record.attribute_id.name))
        return ', '.join(result)
