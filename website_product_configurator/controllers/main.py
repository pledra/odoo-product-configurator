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
        cfg_session = False
        product_config_sessions = request.session.get(
            'product_config_session',
            {}
        )
        is_public_user = request.env.user.has_group('base.group_public')
        if product_config_sessions and product_config_sessions.get(product.id):
            cfg_session = cfg_session_obj.browse(
                int(product_config_sessions.get(product.id))
            )

        # Retrieve and active configuration session or create a new one
        if not cfg_session or not cfg_session.exists():
            cfg_session = cfg_session_obj.sudo().create_get_session(
                product.id,
                force_create=is_public_user,
                user_id=request.env.user.id
            )
            if product_config_sessions:
                request.session['product_config_session'].update({
                    product.id: cfg_session.id
                })
            else:
                request.session['product_config_session'] = {
                    product.id: cfg_session.id
                }
        if (cfg_session.user_id.has_group('base.group_public') and not
                is_public_user):
            cfg_session.user_id = request.env.user

        # Render the configuration template based on the configuration session
        config_form = self.render_form(cfg_session)

        return config_form

    def get_render_vals(self, cfg_session):
        """Return dictionary with values required for website template
        rendering"""

        cfg_session = cfg_session.sudo()
        vals = {
            'cfg_session': cfg_session,
            'cfg_step_lines': cfg_session.get_open_step_lines(),
            'active_step': cfg_session.get_active_step(),
            'value_ids': cfg_session.value_ids.ids,
            'available_value_ids': cfg_session.values_available(),
            'main_object': cfg_session.product_tmpl_id
        }

        return vals

    def render_form(self, cfg_session):
        """Render the website form for the given template and configuration
        session"""
        vals = self.get_render_vals(cfg_session)
        return request.render(
            'website_product_configurator.product_configurator', vals
        )

    @http.route('/website_product_configurator/onchange',
                type='json', methods=['POST'], auth="public", website=True)
    def onchange(self, form_values, field_name):
        """Capture onchange events in the website and forward data to backend
        onchange method"""
        import pdb
        pdb.set_trace()
        for form_val in form_values:
            pass
