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
        website_tmpl_xml_id = ''
        if self.website_tmpl_id:
            website_tmpl_xml_id = self.website_tmpl_id.xml_id
        ICPSudo.set_param(
            'product_configurator.default_configuration_step_website_view_id',
            website_tmpl_xml_id
        )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        xml_id = ICPSudo.get_param(
            'product_configurator.default_configuration_step_website_view_id'
        )

        website_tmpl_xml_id = False
        if xml_id and len(xml_id.split('.')) == 2:
            model_data_id = self.env['ir.model.data'].search([
                ('module', '=', xml_id.split('.')[0]),
                ('name', '=', xml_id.split('.')[1])
            ])
            if model_data_id:
                website_tmpl_id = self.env[model_data_id.model].browse(
                    model_data_id.res_id)
                if (website_tmpl_id.inherit_id.xml_id ==
                        'website_product_configurator.config_form_base'):
                    website_tmpl_xml_id = website_tmpl_id.id

        res.update({'website_tmpl_id': website_tmpl_xml_id})

        return res
