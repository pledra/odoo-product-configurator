# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductConfigStep(models.Model):
    _inherit = 'product.config.step'

    """Extend the configuration step with a selectable view that will
    display the content in the frontend for each separate step"""

    view_id = fields.Many2one(
        comodel_name='ir.ui.view',
        string='Website View',
        domain=lambda s: [(
            'inherit_id', '=', s.env.ref(
                'website_product_configurator.config_form_base').id
        )],
        help="Specific view for rendering this attribute in the frontend"
    )


class ProductConfigSession(models.Model):
    _inherit = 'product.config.session'

    """Set SID for public user. There is no other way to distinguish between
    users that are not logged in with a personal username"""

    session_id = fields.Char(
        string='Session ID',
        help='Website session ID to identify user'
    )
    website = fields.Boolean(
        string='Website',
        help='Used to filter website configuration session from others'
    )
