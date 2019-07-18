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
        ICPSudo.set_param('website_tmpl_id', self.website_tmpl_id.id)


    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update({'website_tmpl_id': int(ICPSudo.get_param(
            'website_tmpl_id'))})

        return res
