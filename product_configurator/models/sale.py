# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class sale_order_line_attribute(models.Model):
#     _name = 'sale.order.line.attribute'

#     custom_value = fields.Char('Custom Value', size=64)
#     sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_value_ids = fields.One2many(
        comodel_name='product.attribute.value.custom',
        inverse_name='product_id',
        related="product_id.value_custom_ids",
        string="Custom Values"
    )

    product_id = fields.Many2one(domain=[('config_ok', '=', False)])

    @api.multi
    def copy(self, default=None):
        """ Ensure when a line is copied, it creates to a new configuration,
        not just points to the original. Without this, changing one
        configuration changes everywhere it appears.
        """
        if default is None:
            default = {}
        if 'product_id' not in default and self.product_id.config_ok:
            default['product_id'] = self.product_id.copy_configurable().id
        return super(SaleOrderLine, self).copy(default=default)
