# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_tmpl_id = fields.Many2one(
        'ir.ui.view', 'Website Template',
        domain=lambda s: [
            ('inherit_id', '=', s.env.ref(
                'website_product_configurator.config_form_base').id)
        ],
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            'product_configurator.configuration_step_view_id',
            self.website_tmpl_id.xml_id)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        website_tmpl = ICPSudo.get_param(
            'product_configurator.configuration_step_view_id')

        if not website_tmpl or len(website_tmpl.split('.')) != 2:
            website_tmpl = 'website_product_configurator.config_form_select'

        website_tmpl_id = self.env['ir.model.data'].search([
            ('module', '=', website_tmpl.split('.')[0]),
            ('name', '=', website_tmpl.split('.')[1])])

        if not website_tmpl_id:
            website_tmpl = 'website_product_configurator.config_form_select'
            website_tmpl_id = self.env['ir.model.data'].search([
                ('module', '=', website_tmpl.split('.')[0]),
                ('name', '=', website_tmpl.split('.')[1])])

        res.update({'website_tmpl_id': website_tmpl_id.res_id})

        return res
