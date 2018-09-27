from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_config_start(self):
        """Return action to start configuration wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator.sale',
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_order_id=self.id,
                wizard_model='product.configurator.sale',
            ),
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    custom_value_ids = fields.One2many(
        comodel_name='product.attribute.value.custom',
        inverse_name='product_id',
        related="product_id.value_custom_ids",
        string="Custom Values"
    )
    config_ok = fields.Boolean(
        related='product_id.config_ok',
        string="Configurable"
    )

    @api.multi
    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""
        wizard_model = 'product.configurator.sale'

        extra_vals = {
            'order_id': self.order_id.id,
            'order_line_id': self.id,
            'product_id': self.product_id.id,
        }

        self = self.with_context({
            'default_order_id': self.order_id.id,
            'default_order_line_id': self.id
        })

        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )
