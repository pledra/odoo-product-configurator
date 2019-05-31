from odoo import fields, models
from datetime import timedelta


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
        default_view_id = 'website_product_configurator.config_form_radio'
        return self.website_tmpl_id.get_xml_id() or default_view_id


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    def remove_inactive_config_sessions(self):
        check_date = fields.Datetime.from_string(
            fields.Datetime.now()) - timedelta(days=3)
        sessions_to_remove = self.search([
            ('write_date', '<', fields.Datetime.to_string(check_date))
        ])
        if sessions_to_remove:
            sessions_to_remove.unlink()
