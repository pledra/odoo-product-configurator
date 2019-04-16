from odoo import fields, models


class ProductConfigStepLine(models.Model):
    _inherit = 'product.config.step.line'

    website_tmpl_id = fields.Many2one(
        string='Website Template',
        comodel_name='ir.ui.view',
        domain=lambda s: [(
            'inherit_id', '=', s.env.ref(
                'website_product_configurator.config_form_base').id
        )],
    )

    def get_website_template(self):
        """Return the external id of the qweb template linked to this step"""
        default_view_id = 'website_product_configurator.config_form_select'
        return self.website_tmpl_id.get_xml_id() or default_view_id
