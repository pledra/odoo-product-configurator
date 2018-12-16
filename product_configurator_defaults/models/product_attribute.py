# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'

    default = fields.Many2one(
        'product.attribute.value',
        string='Default Value',
        help='If set, it will be added by default when no value is selected',
    )
    
    @api.onchange('value_ids')
    def _onchange_value_ids(self):
        # clear default value
        if self.default not in self.value_ids:
            self.default = False

    @api.constrains('value_ids', 'default')
    def _check_default_value(self):
        for rec in self:
            if rec.default and rec.default.id not in rec.value_ids.ids:
                raise ValidationError(_(
                    'Default value "%s" is not included '
                    'in the possible values for this attribute.\r\n'
                    '%s') % (
                        rec.default.display_name,
                        '\r\n'.join(['- %s' % r.display_name for r in rec.value_ids])
                    ))
