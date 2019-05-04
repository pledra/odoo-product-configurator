from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.http_routing.models.ir_http import slug


def get_pricelist():
    sale_order = request.env.context.get('sale_order')
    if sale_order:
        pricelist = sale_order.pricelist_id
    else:
        partner = request.env.user.partner_id
        pricelist = partner.property_product_pricelist
    return pricelist


class ProductConfigWebsiteSale(WebsiteSale):

    # TODO :: remaining part : FOR CUSTOM

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

        # Set config-step in config session when it creates from wizard
        # because select state not exist on website
        if not cfg_session.config_step:
            self.set_config_next_step(cfg_session)

        # Render the configuration template based on the configuration session
        config_form = self.render_form(cfg_session)

        return config_form

    def get_render_vals(self, cfg_session):
        """Return dictionary with values required for website template
        rendering"""

        # if no config step exist
        open_cfg_step_lines = cfg_session.get_open_step_lines()
        active_step = cfg_session.get_active_step()
        cfg_step_lines = cfg_session.get_all_step_lines()
        check_val_ids = cfg_session.product_tmpl_id.attribute_line_ids.mapped(
            'value_ids')
        available_value_ids = cfg_session.values_available(
            check_val_ids=check_val_ids.ids)
        if not active_step:
            active_step = cfg_step_lines[:1]
        vals = {
            'cfg_session': cfg_session,
            'cfg_step_lines': cfg_step_lines,
            'open_cfg_step_lines': open_cfg_step_lines,
            'active_step': active_step,
            'value_ids': cfg_session.value_ids.ids,
            'available_value_ids': available_value_ids,
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

    def remove_prefix(self, values):
        """Remove field prefix from dynamic field name
        before sending data to js"""
        product_configurator_obj = request.env['product.configurator']
        field_prefix = product_configurator_obj._prefixes.get('field_prefix')
        custom_field_prefix = product_configurator_obj._prefixes.get(
            'custom_field_prefix')
        new_values = {}
        for key, value in values.items():
            key = key.replace(field_prefix, '').replace(
                custom_field_prefix, '')
            new_values[key] = value
        return new_values

    def remove_recursive_list(self, values):
        """Return dictionary by removing extra list
        :param: values: dictionary having values in form [[4, 0, [2, 3]]]
        :return: dictionary 
        EX- {2: [2, 3]}"""
        new_values = {}
        for key, value in values.items():
            if isinstance(value, tuple):
                value = value[0]
            if isinstance(value, list):
                value = value[0][2]
            new_values[key] = value
        return new_values

    def get_current_configuration(self, form_values,
                                  cfg_session, product_tmpl_id):
        """Return list of value ids same as
        we store in value_ids in session"""
        product_attribute_lines = product_tmpl_id.attribute_line_ids
        value_ids = []
        for attr_line in product_attribute_lines:
            if attr_line.custom:
                pass
            else:
                attr_values = form_values.get(attr_line.attribute_id.id, False)
                if not attr_values:
                    continue
                if not isinstance(attr_values, list):
                    attr_values = [attr_values]
                value_ids += attr_values
        return value_ids

    def update_dynamic_fields(self, product_tmpl_id, form_vals):
        product_configurator_obj = request.env['product.configurator']
        field_prefix = product_configurator_obj._prefixes.get('field_prefix')
        # custom_field_prefix = product_configurator_obj._prefixes.get(
        #    'custom_field_prefix')

        attr_lines = product_tmpl_id.attribute_line_ids.sorted()
        vals = {}
        for attr_line in attr_lines:
            attribute_id = attr_line.attribute_id.id
            field_name = '%s%s' % (field_prefix, attribute_id)
            # custom_field = '%s%s' % (custom_field_prefix, attribute_id)
            field_value = form_vals.get(attribute_id, False)
            # custom_field_value = form_vals.get('%s' % (custom_field), False)
            if attr_line.custom:
                pass

            elif attr_line.multi:
                if not field_value:
                    field_value = []
                field_value = [[6, False, field_value]]

            vals.update({
                field_name: field_value,
                # custom_field: form_vals.get(
                #    '%s' % (custom_field), False) or False,
            })
        return vals

    def _prepare_configurator_values(self, form_vals, config_session_id,
                                     product_tmpl_id):
        config_fields = {
            'state': config_session_id.state,
            'config_session_id': config_session_id.id,
            'product_tmpl_id': product_tmpl_id.id,
            'product_preset_id': config_session_id.product_preset_id.id,
            'price': config_session_id.price,
            'value_ids': [[6, False, config_session_id.value_ids.ids]],
            'attribute_value_line_ids': [
                [4, line.id, False]
                for line in config_session_id.attribute_value_line_ids
            ],
            'attribute_line_ids': [
                [4, line.id, False]
                for line in product_tmpl_id.attribute_line_ids
            ],
        }
        config_fields.update(self.update_dynamic_fields(
            product_tmpl_id, form_vals))
        return config_fields

    def get_dictionary_from_form_vals(self, form_vals,
                                      config_session, product_tmpl_id):
        values = {}
        for form_val in form_vals:
            if form_val['name'] in values and form_val['value']:
                values[form_val['name']].append(form_val['value'])
            else:
                value = form_val['value'] and [form_val['value']] or []
                values.update({form_val['name']: value})

        config_vals = {}
        for attr_line in product_tmpl_id.attribute_line_ids:
            if attr_line.custom:
                pass
            else:
                attr_vals = values.get('%s' % (attr_line.attribute_id.id), [])
                attr_vals = [int(s) for s in attr_vals]
                if not attr_line.multi:
                    attr_vals = attr_vals and attr_vals[0] or False
                config_vals.update({
                    attr_line.attribute_id.id: attr_vals
                })
        return config_vals

    def get_session_and_product(self, form_vals):
        product_template_id = request.env['product.template']
        config_session = request.env['product.config.session']
        for val in form_vals:
            if val.get('name') == 'product_tmpl_id':
                product_tmpl_id = val.get('value')
            if val.get('name') == 'config_session_id':
                config_session_id = val.get('value')

        if product_tmpl_id:
            product_template_id = product_template_id.browse(
                int(product_tmpl_id))
        if config_session_id:
            config_session = config_session.browse(
                int(config_session_id))
        return {
            'config_session': config_session,
            'product_tmpl': product_template_id
        }

    @http.route('/website_product_configurator/onchange',
                type='json', methods=['POST'], auth="public", website=True)
    def onchange(self, form_values, field_name):
        """Capture onchange events in the website and forward data to backend
        onchange method"""
        product_configurator_obj = request.env['product.configurator']
        result = self.get_session_and_product(form_values)
        config_session_id = result.get('config_session')
        product_template_id = result.get('product_tmpl')

        form_values = self.get_dictionary_from_form_vals(
            form_values, config_session_id, product_template_id)
        config_vals = self._prepare_configurator_values(
            form_values, config_session_id, product_template_id)

        field_prefix = product_configurator_obj._prefixes.get('field_prefix')
        field_name = '%s%s' % (field_prefix, field_name)
        specs = product_configurator_obj._onchange_spec()
        updates = product_configurator_obj.onchange(
            config_vals, field_name, specs)

        value_ids = self.get_current_configuration(
            form_values, config_session_id, product_template_id)
        open_cfg_step_lines = config_session_id.get_open_step_lines(value_ids)

        updates['value'] = self.remove_prefix(updates['value'])
        updates['value'] = self.remove_recursive_list(updates['value'])
        updates['domain'] = self.remove_prefix(updates['domain'])
        updates['open_cfg_step_lines'] = open_cfg_step_lines.ids
        return updates

    def set_config_next_step(self, config_session_id, next_step=False):
        # TODO :: If no config step exist
        if not next_step:
            adjacent_steps = config_session_id.get_adjacent_steps()
            next_step = adjacent_steps.get('next_step', False)
            if next_step:
                next_step = '%s' % (next_step.id)
        if next_step:
            config_session_id.config_step = next_step
        return next_step

    @http.route('/website_product_configurator/save_configuration',
                type='json', methods=['POST'], auth="public", website=True)
    def save_configuration(self, form_values, next_step=False):
        product_configurator_obj = request.env['product.configurator']
        result = self.get_session_and_product(form_values)
        config_session_id = result.get('config_session')
        product_template_id = result.get('product_tmpl')

        form_values = self.get_dictionary_from_form_vals(
            form_values, config_session_id, product_template_id)
        try:
            config_session_id.update_config(attr_val_dict=form_values)
            next_step = self.set_config_next_step(config_session_id, next_step)
            if next_step:
                return {'next_step': next_step}
            product = config_session_id.create_get_variant()
            if product:
                redirect_url = "/website_product_configurator/open_product"
                redirect_url += '/%s' % (slug(config_session_id))
                redirect_url += '/%s' % (slug(product))
                return {
                    'product_id': product.id,
                    'config_session': config_session_id.id,
                    'redirect_url': redirect_url,
                }
        except Exception as Ex:
            return {'error': Ex}
        return {}

    @http.route(
        '/website_product_configurator/open_product/<model("product.config.session"):cfg_session>/<model("product.product"):product_id>',
        type='http', auth="public", website=True)
    def cfg_session(self, cfg_session, product_id, **post):
        try:
            product_tmpl = cfg_session.product_tmpl_id
        except:
            product_tmpl = product_id.product_tmpl_id

        def _get_product_vals(cfg_session):
            vals = cfg_session.value_ids
            # vals += cfg_session.custom_value_ids
            return sorted(vals, key=lambda obj: obj.attribute_id.sequence)

        pricelist = get_pricelist()
        values = {
            'get_product_vals': _get_product_vals,
            # 'get_config_image': self.get_config_image,
            'product_id': product_id,
            'product_tmpl': product_tmpl,
            'pricelist': pricelist,
            'cfg_session': cfg_session,
        }
        return request.render(
            "website_product_configurator.cfg_session", values)
