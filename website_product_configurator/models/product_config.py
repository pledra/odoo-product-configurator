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
        view_id = self.env[
            'product.config.session'].check_config_form_template()
        if self.website_tmpl_id:
            xml_id_dict = self.website_tmpl_id.get_xml_id()
            view_id = xml_id_dict.get(self.website_tmpl_id.id)
        return view_id


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

    def check_config_form_template(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        website_tmpl = ICPSudo.get_param(
            'product_configurator.configuration_step_view_id')

        if not website_tmpl or len(website_tmpl.split('.')) != 2:
            return 'website_product_configurator.config_form_select'

        website_tmpl_id = self.env['ir.model.data'].search([
            ('module', '=', website_tmpl.split('.')[0]),
            ('name', '=', website_tmpl.split('.')[1])])

        if not website_tmpl_id:
            return 'website_product_configurator.config_form_select'

        return website_tmpl
