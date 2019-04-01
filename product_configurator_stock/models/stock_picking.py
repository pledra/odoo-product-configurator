from odoo import models, api, fields


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    allow_configuration = fields.Boolean(
        string="Allow configuration",
        default=False)


class Picking(models.Model):
    _inherit = 'stock.picking'

    allow_configuration = fields.Boolean(
        related='picking_type_id.allow_configuration',
        string="Allow configuration")

    @api.multi
    def action_config_start(self):
        """Return action to start configuration wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator.picking',
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                default_picking_id=self.id,
                wizard_model='product.configurator.picking',
            ),
        }
