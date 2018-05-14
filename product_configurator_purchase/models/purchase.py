from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_config_start(self):
        """Return action to start configuration wizard"""
        wizard_model = 'product.configurator.purchase'
        return {
            'type': 'ir.actions.act_window',
            'res_model': wizard_model,
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_order_id=self.id,
                wizard_model=wizard_model,
            ),
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    config_ok = fields.Boolean(
        related='product_id.config_ok',
        string="Configurable"
    )
    parent_state = fields.Selection(
        related='order_id.state'
    )

    @api.multi
    def reconfigure_product(self):
        """Create and launch a product configurator wizard with a linked
        purchase order line to edit the configurable product"""

        wizard_model = 'product.configurator.purchase'
        cfg_steps = self.product_id.product_tmpl_id.config_step_line_ids
        active_step = str(cfg_steps[0].id) if cfg_steps else 'configure'

        wizard_obj = self.env[wizard_model]
        wizard = wizard_obj.create({
            'product_id': self.product_id.id,
            'state': active_step,
            'order_id': self.order_id.id,
            'order_line_id': self.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': wizard_model,
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=wizard.id,
                wizard_model=wizard_model
            ),
            'target': 'new',
            'res_id': wizard.id,
        }
