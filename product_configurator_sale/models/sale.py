# -*- coding: utf-8 -*-

from openerp import models, fields, api


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
    config_ok = fields.Boolean(
        related='product_id.config_ok',
        string="Configurable"
    )

    @api.multi
    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""

        cfg_steps = self.product_id.product_tmpl_id.config_step_line_ids
        active_step = str(cfg_steps[0].id) if cfg_steps else 'configure'

        wizard_obj = self.env['product.configurator']
        wizard = wizard_obj.create({
            'product_id': self.product_id.id,
            'state': active_step,
            'order_line_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator',
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=wizard.id,
            ),
            'target': 'new',
            'res_id': wizard.id,
        }
