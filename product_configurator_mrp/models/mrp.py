from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.mrp"]
        ctx = dict(
            self.env.context,
            wizard_model="product.configurator.mrp",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(ctx).get_wizard_action()


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    config_ok = fields.Boolean(
        related="product_tmpl_id.config_ok",
        store=True,
        string="Configurable",
        readonly=True,
    )


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    def _skip_bom_line(self, product):
        """ Control if a BoM line should be produce, can be inherited for add
        custom control. It currently checks that all variant values are in the
        product. """
        if not self.bom_id.config_ok:
            return super(MrpBomLine, self)._skip_bom_line(product=product)
        if not self.config_set_id.configuration_ids:
            return False
        product_value_ids = set(
            product.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            ).ids
        )
        for config in self.config_set_id.configuration_ids:
            if len(set(config.value_ids.ids) - product_value_ids) == 0:
                return False
        return True

    config_set_id = fields.Many2one(
        comodel_name="mrp.bom.line.configuration.set",
        string="Configuration Set",
    )


class MrpBomLineConfigurationSet(models.Model):
    _name = "mrp.bom.line.configuration.set"
    _description = "Mrp Bom Line Configuration Set"

    name = fields.Char(string="Configuration", required=True)
    configuration_ids = fields.One2many(
        comodel_name="mrp.bom.line.configuration",
        inverse_name="config_set_id",
        string="Configurations",
    )
    bom_line_ids = fields.One2many(
        comodel_name="mrp.bom.line",
        inverse_name="config_set_id",
        string="BoM Lines",
        readonly=True,
    )


class MrpBomLineConfiguration(models.Model):
    _name = "mrp.bom.line.configuration"
    _description = "Mrp Bom Line Configuration"

    config_set_id = fields.Many2one(
        comodel_name="mrp.bom.line.configuration.set",
        ondelete="cascade",
        required=True,
    )
    value_ids = fields.Many2many(
        string="Attribute Values",
        comodel_name="product.attribute.value",
        required=True,
    )
