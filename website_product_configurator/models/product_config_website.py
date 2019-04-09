from odoo import models, fields
from odoo.http import request
from odoo.exceptions import ValidationError


class ProductConfigWebsite(models.AbstractModel):
    """Model used to render and handle website forms and events"""
    _name = 'product.config.website'

    def create(self, vals):
        """Use the indicated template to create or get a config session"""
        cfg_session = self.env['product.config.session'].create_get_session(
            vals.get('product_tmpl_id')
        )
        del vals['product_tmpl_id']
        vals['config_session_id'] = cfg_session.id
        return super(ProductConfigWebsite, self).create(vals)

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        related='config_session_id.product_tmpl_id',
        string="Configurable Template",
    )
    config_session_id = fields.Many2one(
        comodel_name='product.config.session',
        string='Configuration Session',
        required=True
    )

    def get_render_vals(self, product_tmpl):
        """Return dictionary with values required for website template rendering"""

        vals = {
            'cfg_session': self.cfg_session,
            'cfg_step_lines': self.cfg_session.get_open_step_lines(),
            'active_step': self.cfg_session.get_active_step(),
        }

    def render_form(self, product_tmpl, cfg_session=None):
        """Render the website form for the given template and configuration session"""

        cfg_step_line = cfg_session.get_active_step() or cfg_session.get_open_step_lines()[:1]

        template = cfg_step_line.get_website_template()

        values = self.get_website_context_vals()

        request.render(template, values)
        import pdb;pdb.set_trace()