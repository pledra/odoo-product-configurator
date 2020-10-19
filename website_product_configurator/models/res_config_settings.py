from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_tmpl_id = fields.Many2one(
        comodel_name="ir.ui.view",
        string="Website Template",
        domain=lambda s: [
            (
                "inherit_id",
                "=",
                s.env.ref("website_product_configurator.config_form_base").id,
            )
        ],
    )

    def xml_id_to_record_id(self, xml_id):
        if not xml_id or len(xml_id.split(".")) != 2:
            return False

        website_tmpl_id = self.env.ref(xml_id)
        if (
            website_tmpl_id.exists() and
            website_tmpl_id.inherit_id != self.env.ref(
                "website_product_configurator.config_form_base"
            )
        ):
            return False
        return website_tmpl_id

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env["ir.config_parameter"].sudo()
        website_tmpl_xml_id = ""
        if self.website_tmpl_id:
            website_tmpl_xml_id = self.website_tmpl_id.xml_id
        ICPSudo.set_param(
            "product_configurator.default_configuration_step_website_view_id",
            website_tmpl_xml_id,
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env["ir.config_parameter"].sudo()
        xml_id = ICPSudo.get_param(
            "product_configurator.default_configuration_step_website_view_id"
        )

        website_tmpl_xml_id = self.xml_id_to_record_id(xml_id=xml_id)
        res.update(
            {
                "website_tmpl_id": (
                    website_tmpl_xml_id
                    and website_tmpl_xml_id.id
                    or website_tmpl_xml_id
                )
            }
        )
        return res
