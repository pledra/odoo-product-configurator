from odoo import models, fields


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    allow_configuration = fields.Boolean(
        string="Allow configuration", default=False
    )


class Picking(models.Model):
    _inherit = "stock.picking"

    allow_configuration = fields.Boolean(
        related="picking_type_id.allow_configuration",
        string="Allow configuration",
    )

    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.picking"]
        ctx = dict(
            self.env.context,
            default_picking_id=self.id,
            wizard_model="product.configurator.picking",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(ctx).get_wizard_action()
