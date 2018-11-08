from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_config_start(self):
        """Return action to start configuration wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator.mrp',
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_order_id=self.id,
                wizard_model='product.configurator.mrp',
            ),
        }


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    config_ok = fields.Boolean(
        related='product_tmpl_id.config_ok',
        store=True
    )
