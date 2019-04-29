from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.safe_eval import safe_eval


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

        cfg_step_lines = cfg_session.get_open_step_lines()
        active_step = cfg_session.get_active_step()
        if not active_step:
            active_step = cfg_step_lines[:1]
        vals = {
            'cfg_session': cfg_session,
            'cfg_step_lines': cfg_step_lines,
            'active_step': active_step,
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

    # TODO :: FOR CUSTOM
    def get_dictionary_from_form_vals(self, form_vals):
        config_vals = {}
        for form_val in form_vals:
            if form_val['name'] == 'csrf_token':
                continue
            if form_val['name'] in config_vals and form_val['value']:
                config_vals[form_val['name']].append(form_val['value'])
            else:
                value = form_val['value'] and [form_val['value']] or []
                config_vals.update({form_val['name']: value})
        return config_vals

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
            field_value = form_vals.get('%s' % (attribute_id), [])
            # custom_field_value = form_vals.get('%s' % (custom_field), False)
            if attr_line.custom:
                field_type = attr_line.attribute_id.custom_type
                if field_value and field_type in ['int', 'float']:
                    field_value = safe_eval(field_value[0])
            else:
                field_value = [int(s) for s in field_value]

            if attr_line.multi:
                field_value = [[6, False, field_value]]
            elif field_value:
                field_value = field_value[0]
            else:
                field_value = False

            if attr_line.custom:
                # TODO :: if attribute is custome
                pass

            vals.update({
                field_name: field_value,
                # custom_field: form_vals.get(
                #    '%s' % (custom_field), False) or False,
            })
        return vals

    def _prepare_configurator_values(self, form_vals):
        form_vals = self.get_dictionary_from_form_vals(form_vals)
        product_tmpl_id = [int(p) for p in form_vals.get(
            'product_tmpl_id', [])]
        config_session_id = [int(s) for s in form_vals.get(
            'config_session_id', [])]
        product_template_id = request.env['product.template'].browse(
            product_tmpl_id)
        config_session_id = request.env['product.config.session'].browse(
            config_session_id)

        config_fields = {
            'state': config_session_id.state,
            'config_session_id': config_session_id.id,
            'product_tmpl_id': product_template_id.id,
            'product_preset_id': config_session_id.product_preset_id.id,
            'price': config_session_id.price,
            'value_ids': [[6, False, config_session_id.value_ids.ids]],
            'attribute_value_line_ids': [
                [4, line.id, False]
                for line in config_session_id.attribute_value_line_ids
            ],
            'attribute_line_ids': [
                [4, line.id, False]
                for line in product_template_id.attribute_line_ids
            ],
        }
        config_fields.update(self.update_dynamic_fields(
            product_template_id, form_vals))
        return config_fields

    def remove_prefix(self, values):
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
        new_values = {}
        for key, value in values.items():
            if isinstance(value, list):
                value = value[0][2]
            new_values[key] = value
        return new_values

    @http.route('/website_product_configurator/onchange',
                type='json', methods=['POST'], auth="public", website=True)
    def onchange(self, form_values, field_name):
        """Capture onchange events in the website and forward data to backend
        onchange method"""
        product_configurator_obj = request.env['product.configurator']
        config_vals = self._prepare_configurator_values(form_values)
        field_prefix = product_configurator_obj._prefixes.get('field_prefix')
        field_name = '%s%s' % (field_prefix, field_name)
        specs = product_configurator_obj._onchange_spec()
        updates = product_configurator_obj.onchange(
            config_vals, field_name, specs)
        updates['value'] = self.remove_prefix(updates['value'])
        updates['value'] = self.remove_recursive_list(updates['value'])
        updates['domain'] = self.remove_prefix(updates['domain'])
        return updates
