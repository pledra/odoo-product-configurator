from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductConfigWebsiteSale(WebsiteSale):

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        # Use parent workflow for regular products
        if not product.config_ok:
            return super(ProductConfigWebsiteSale, self).product(
                product, category, search, **kwargs
            )

        cfg_session_obj = request.env['product.config.session']

        # Retrieve and active configuration session or create a new one
        cfg_session = cfg_session_obj.create_get_session(product.id)

        # Render the configuration template based on the configuration session
        config_form = self.render_form(cfg_session)

        return config_form

    def get_render_vals(self, cfg_session):
        """Return dictionary with values required for website template
        rendering"""

        vals = {
            'cfg_session': cfg_session,
            'cfg_step_lines': cfg_session.get_open_step_lines(),
            'active_step': cfg_session.get_active_step(),
            'value_ids': cfg_session.value_ids,
            'available_value_ids': cfg_session.values_available(),
            'main_object': cfg_session.product_tmpl_id
        }

        return vals

    def render_form(self, cfg_session):
        """Render the website form for the given template and configuration
        session"""

        vals = self.get_render_vals(cfg_session)
        cfg_step_line = vals.get('active_step', vals.get('cfg_step_lines')[:1])

        # TODO: Implement method to select template from step line if
        # applied or config step if not
        template = cfg_step_line.get_website_template()

        return request.render(template, vals)
