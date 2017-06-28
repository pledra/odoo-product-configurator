# -*- coding: utf-8 -*-

import json
import base64
from werkzeug import secure_filename

from odoo import http
from odoo.http import request
from odoo.addons.website.models.website import slug
from odoo.addons.website_sale.controllers import main


def get_pricelist():
    sale_order = request.env.context.get('sale_order')
    if sale_order:
        pricelist = sale_order.pricelist_id
    else:
        partner = request.env.user.partner_id
        pricelist = partner.property_product_pricelist
    return pricelist


class WebsiteProductConfig(http.Controller):

    # Frequently used url's in http route
    cfg_tmpl_url = '/configurator/<model("product.template"):product_tmpl>'
    cfg_step_url = (cfg_tmpl_url +
                    '/<model("product.config.step.line"):config_step>')

    attr_field_prefix = 'attribute_'
    custom_attr_field_prefix = 'custom_attribute_'

    def get_pricelist(self):
        return get_pricelist()

    def get_json_config(self, product_tmpl, json_code, config_step=None):
        """ Computes the configuration code by taking form values sent from
            the frontend and intersects them with the session configuration
            values. Thus having a updated configuration code without storing
            the result in the database.

            :param product_tmpl: product.template object being configured
            :param json_code: arraySerialized object representing client form
            :param config_step: current product.config.step.line object

            :returns: configuraton code dictionary
        """
        # Convert json data to post-like data

        json_vals = {}
        for d in json_code:
            field_name = d.get('name')
            field_val = d.get('value')
            if field_name not in json_vals:
                json_vals[field_name] = field_val
            else:
                if not isinstance(json_vals[field_name], list):
                    json_vals[field_name] = [json_vals[field_name]]
                json_vals[field_name].append(field_val)

        parsed_vals = self.config_parse(product_tmpl, json_vals, config_step)

        cfg_session = self.get_cfg_session(product_tmpl)
        attr_lines = product_tmpl.attribute_line_ids

        # If the template has configuration steps limit only to the active one
        if config_step:
            attr_lines = config_step.attribute_line_ids

        attr_ids = attr_lines.mapped('attribute_id').ids

        # Remove values from the configuration step (if any, all otherwise)
        attr_vals_dict = {
            val.attribute_id.id: val.id for val in cfg_session.value_ids
            if val.attribute_id.id not in attr_ids
        }

        custom_vals_dict = {
            l.attribute_id.id: l.value or l.attachment_ids for l in
            cfg_session.custom_value_ids if l.attribute_id.id not in attr_ids
        }

        parsed_attr_vals_dict = {
            int(k.split(self.attr_field_prefix)[1]): v
            for k, v in parsed_vals['cfg_vals'].iteritems()
        }

        parsed_custom_vals_dict = {
            int(k.split(self.custom_attr_field_prefix)[1]): v
            for k, v in parsed_vals['custom_vals'].iteritems()
        }

        attr_vals_dict.update(parsed_vals['cfg_vals'])
        custom_vals_dict.update(parsed_vals['custom_vals'])

        return {
            'attr_vals': parsed_attr_vals_dict,
            'custom_vals': parsed_custom_vals_dict
        }

    @http.route([
        cfg_tmpl_url + '/value_onchange',
        cfg_step_url + '/value_onchange'
    ], type='json', auth='public', website=True)
    def value_onchange(self, product_tmpl, config_step=None, cfg_vals=None):
        """ Check attribute domain restrictions on each value change and
            combine the form data sent from the frontend with the stored
            configured in the session

            :param product_tmpl: product.template object being configured
            :param config_step: current product.config.step object
            :param cfg_vals: arraySerialized object representing client form

            :returns: list of available ids for all options in the form
        """

        json_config = self.get_json_config(product_tmpl, cfg_vals, config_step)
        cfg_val_ids = product_tmpl.flatten_val_ids(
            json_config['attr_vals'].values())
        attr_lines = product_tmpl.attribute_line_ids

        if config_step:
            cfg_session = self.get_cfg_session(product_tmpl, force_create=True)
            attr_lines = config_step.attribute_line_ids
            cfg_val_ids += cfg_session.value_ids.filtered(
                lambda x: x not in attr_lines.mapped('value_ids')).ids

        attr_vals = attr_lines.mapped('value_ids')

        vals = {
            'value_ids': product_tmpl.values_available(
                attr_vals.ids, cfg_val_ids),
            'prices': product_tmpl.get_cfg_price(
                cfg_val_ids, json_config['custom_vals'], formatLang=True),
        }
        return vals

    # TODO: Use the same variable name all over cfg_val, cfg_step, no mixup
    # TODO: Rename cfg_vars to cfg_env everywhere, possibly turn into object
    def config_vars(self, product_tmpl, active_step=None, data=None):
        """ Proccess configuration step variables from the product.template

        :param product_tmpl: product.template object being configured
        :param active_step: current product.config.step.line object
        :returns: dict of config related variables
        """
        if data is None:
            data = {}

        attr_lines = product_tmpl.attribute_line_ids
        cfg_lines = product_tmpl.config_line_ids
        config_steps = product_tmpl.config_step_line_ids

        custom_value = request.env.ref(
            'product_configurator.custom_attribute_value')

        cfg_session = self.get_cfg_session(product_tmpl, force_create=True)

        # TODO: Set default view in config parameters
        vals = {
            'attr_lines': attr_lines,
            'cfg_lines': cfg_lines,
            'view_id': 'website_product_configurator.config_form_select',
            'cfg_session': cfg_session,
            'attr_field_prefix': self.attr_field_prefix,
            'custom_attr_field_prefix': self.custom_attr_field_prefix
        }

        if not config_steps:
            return vals

        if not active_step:
            active_step = config_steps[0]

        if active_step not in config_steps:
            return vals

        cfg_step_lines = active_step.attribute_line_ids

        adjacent_steps = product_tmpl.get_adjacent_steps(
            cfg_session.value_ids.ids, active_step_line_id=active_step.id)

        vals.update({
            'config_steps': config_steps,
            'custom_value': custom_value,
            'active_step': active_step,
            'view_id': active_step.config_step_id.view_id.xml_id,
            'next_step': adjacent_steps.get('next_step'),
            'previous_step': adjacent_steps.get('previous_step'),
            'cfg_step_lines': cfg_step_lines,
        })
        return vals

    @http.route('/configurator/', auth='public', website=True)
    def select_template(self, **kw):

        template_obj = request.env['product.template']
        templates = template_obj.search([('config_ok', '=', True)])
        tmpl_ext_id = 'website_product_configurator.product_configurator_list'

        style_obj = request.env['product.style']
        styles = style_obj.search([])

        keep = main.QueryURL('/configurator')

        values = {
            'templates': templates,
            'bins': main.TableCompute().process(templates),
            'styles': styles,
            'keep': keep,
            'rows': main.PPR,
            'style_in_product': lambda style, product: style.id in [
                s.id for s in product.website_style_ids],
        }
        return request.render(tmpl_ext_id, values)

    def parse_upload_file(self, field_name, multi=False):
        """ Parse uploaded file from request.files """
        # TODO: Set allowed extensions in the backend and compare
        files = request.httprequest.files.getlist(field_name)
        attachments = []
        for file in files:
            attachments.append({
                'name': secure_filename(file.filename),
                'datas': base64.b64encode(file.stream.read())
            })
            if not multi:
                return attachments
        return attachments

    def parse_config_post(self, product_tmpl):
        """
        Parses the form data from the request object using the attribute
        lines on the product_template as a filter

        The default parsing method of the post values from werkzeug
        does not support muliple values and single values mixed in
        one post

        :param product_tmpl: product.template object being configured

        :returns: dict of parsed configuration values
        """
        config_code = {}
        post = request.httprequest.form
        attr_lines = product_tmpl.attribute_line_ids
        for line in attr_lines:
            field_name = self.attr_field_prefix + str(line.attribute_id.id)
            custom_field_name = self.custom_attr_field_prefix + str(
                line.attribute_id.id)
            if field_name not in post:
                continue
            val = post.get(field_name)
            if val == 'custom':
                custom_type = line.attribute_id.custom_type
                if custom_type == 'binary':
                    custom_val = self.parse_upload_file(
                        custom_field_name, line.multi)
                else:
                    class_mapper = {'int': int, 'float': float}
                    custom_type = class_mapper.get(custom_type, None)
                    # For numerical values force datatype
                    custom_val = post.get(custom_field_name, type=custom_type)
                config_code.update({
                    field_name: 'custom',
                    custom_field_name: custom_val
                })
                continue
            if line.multi:
                # Return a list if multiple values are allowed
                val = request.httprequest.form.getlist(
                    field_name, type=int)
            else:
                val = post.get(field_name, type=int)
            config_code[field_name] = val
        return config_code

    def config_update(self, parsed_vals, cfg_session):
        """
        Update the session with the configuration values related to
        product template passed in the product_tmpl argument.

        :param vals: dictionary containing the parsed configuration values
        :param config_session: product.config.session object representing
                               curent configuration
        """

        vals_dict = {
            int(field_name.split(self.attr_field_prefix)[1]): val
            for field_name, val in parsed_vals['cfg_vals'].iteritems()
        }

        custom_vals_dict = {
            int(field_name.split(self.custom_attr_field_prefix)[1]): val
            for field_name, val in parsed_vals['custom_vals'].iteritems()
        }

        binary_custom_vals = cfg_session.custom_value_ids.filtered(
            lambda x: x.attachment_ids)

        # Ignore empty vals for attachments if they are already on the session
        for attr_id in custom_vals_dict.keys():
            val = custom_vals_dict[attr_id]
            if not val and attr_id in binary_custom_vals.ids:
                del custom_vals_dict[attr_id]

        cfg_session.sudo().update_config(vals_dict, custom_vals_dict)

        return True

    @http.route([
        cfg_tmpl_url + '/config_clear',
        cfg_step_url + '/config_clear'
    ], type='json', auth='public', website=True)
    def config_clear(self, product_tmpl, **kwargs):
        """
        Remove the configuration stored in session for the specified
        product template.

        :param product_tmpl: product.template object being configured
        :returns: True
        """
        self.get_cfg_session(product_tmpl).sudo().unlink()
        reload_link = '/configurator/%s' % slug(product_tmpl)
        return reload_link

    def config_parse(self, product_tmpl, post, config_step=None,
                     force_require=False):
        """
        Validate the configuration data inside the post dictionary

        Contains the active config_step as a parameter so when extending
        this method separate validation logic can be applied for each step
        if needed

        :param product_tmpl: product.template object being configured
        :param post: sanitized configuration dict from frontend
        :param active_step: current product.config.step.line
        :param force_require: force required fields regardless of availability
        :returns: dict of sanitized values and errors encountered
        """
        # TODO: Verify if option is selectable with current configuration
        values = {
            'cfg_vals': {},
            'custom_vals': {},
            'errors': {}
        }
        attr_lines = product_tmpl.attribute_line_ids
        if config_step:
            attr_lines = config_step.attribute_line_ids

        required_lines = attr_lines.filtered('required')

        for line in attr_lines:
            attr_id = line.attribute_id.id
            field_name = self.attr_field_prefix + str(attr_id)
            custom_field_name = self.custom_attr_field_prefix + str(attr_id)
            if not post.get(field_name):
                values['cfg_vals'].update({field_name: None})
                if line in required_lines and force_require:
                    values['errors'][field_name] = 'missing'
                # else:
                #     lock_vals = product_tmpl.get_lock_vals(attr_id)
                #     if not lock_vals or parent_val not in lock_vals.ids:
                #         values['errors'][field_name] = 'missing'
                continue
            try:
                if post.get(field_name) == 'custom':
                    if not line.custom:
                        continue
                    custom_val = post.get(custom_field_name)
                    if custom_val:
                        custom_type = line.attribute_id.custom_type
                        if custom_type in ['float', 'integer']:
                            max_val = line.attribute_id.max_val
                            min_val = line.attribute_id.min_val
                            if max_val and custom_val > max_val:
                                continue
                            elif min_val and custom_val < min_val:
                                continue
                        values['custom_vals'].update({
                            custom_field_name: custom_val})
                        values['cfg_vals'].update({
                            field_name: 'custom'
                        })
                    else:
                        if line in required_lines:
                            values['errors'][field_name] = 'missing'
                    continue

                if line.multi:
                    # Attempt conversion to list for multi values
                    if not isinstance(post[field_name], list):
                        try:
                            post[field_name] = [post[field_name]]
                        except:
                            continue
                    post_vals = {int(val) for val in post[field_name]}
                    line_vals = set(line.value_ids.ids)
                    vals = post_vals.intersection(line_vals)
                    if not vals:
                        values['errors'][field_name] = 'invalid'
                    else:
                        values['cfg_vals'].update({
                            field_name: list(vals)})
                else:
                    try:
                        val_id = int(post[field_name])
                    except:
                        val_id = None
                    if val_id not in line.value_ids.ids:
                        values['errors'][field_name] = 'invalid'
                    else:
                        values['cfg_vals'].update({field_name: val_id})
            except ValueError:
                values['errors'][field_name] = 'invalid'
        return values

    def config_redirect(self, product_tmpl, config_step, post=None,
                        value_ids=None, custom_vals=None):
        """
        Redirect user to a certain url depending on the configuration state
        """
        if post is None:
            post = {}
        if value_ids is None:
            value_ids = []
        if custom_vals is None:
            custom_vals = {}

        cfg_steps = product_tmpl.config_step_line_ids

        product_tmpl_url = '/configurator/%s' % slug(product_tmpl)

        if not cfg_steps:
            # If there are no config steps and there's a post
            # it is a final one-step configuration
            if post:
                valid_config = product_tmpl.validate_configuration(
                    value_ids, custom_vals)
                if valid_config:
                    return None
                else:
                    return request.redirect(product_tmpl_url)
            return None

        # Redirect the user towards the first step if they exist
        elif cfg_steps and not config_step:
            return request.redirect(
                '%s/%s' % (product_tmpl_url, slug(cfg_steps[0]))
            )

        # TODO: Do not allow dependencies to be set on the first config step
        if config_step == cfg_steps[0] and not post:
            return False

        # elif product_tmpl.id not in cfg_session and config_step
        # != cfg_steps[0]:
        #     return request.redirect(product_tmpl_nurl)

        for i, line in enumerate(cfg_steps):
            if config_step == line:
                try:
                    next_step = cfg_steps[i + 1]
                except:
                    next_step = None

        open_steps = product_tmpl.get_open_step_lines(value_ids)

        if post:
            if next_step:
                return request.redirect(
                    '%s/%s' % (product_tmpl_url, slug(next_step))
                )

            # If this is the last step then validation and creation is next
            valid_config = product_tmpl.validate_configuration(
                value_ids, custom_vals)
            if not valid_config:
                return request.redirect(
                    '%s/%s' % (product_tmpl_url, slug(open_steps[0]))
                )
            else:
                return None

        elif config_step and config_step not in open_steps:
            if next_step:
                return request.redirect(
                    '%s/%s' % (product_tmpl_url, slug(next_step))
                )
            return request.redirect(
                '%s/%s' % (product_tmpl_url, slug(open_steps[0]))
            )
        return None

    def product_redirect(self, cfg_session):
        return request.redirect('/configurator/config/%s' % slug(cfg_session))

    def get_cfg_session(self, product_tmpl, force_create=False):
        """Retrieve the product.config.session from backend holding all the
        configuration data stored so far by this user for the designated
        product template object"""

        public_user_id = request.env.ref('base.public_user').id

        cfg_session_obj = request.env['product.config.session']

        domain = [
            ('product_tmpl_id', '=', product_tmpl.id),
            ('user_id', '=', request.env.user.id),
            ('website', '=', True),
            ('state', '=', 'draft')
        ]

        if request.env.uid == public_user_id:
            domain.append(('session_id', '=', request.session.sid))

        cfg_session = cfg_session_obj.search(domain)

        if not cfg_session and force_create:
            vals = {
                'product_tmpl_id': product_tmpl.id,
                'user_id': request.env.user.id,
                'website': True
            }

            if request.env.uid == public_user_id:
                vals.update(session_id=request.session.sid)

            cfg_session = cfg_session_obj.sudo().create(vals)

        return cfg_session

    def get_config_image(self, product_tmpl, value_ids, size=None):
        """
        Retreive the image that most closely resembles the configuration
        code sent via cfg_vals dictionary

        :param product_tmpl: product.template object being configured
        :param cfg_vals: a list representing the ids of attribute values
                         (usually stored in the user's session)
        :returns: path to the selected image
        """
        # TODO: Also consider custom values for image change
        img_obj = product_tmpl.sudo().get_config_image_obj(value_ids, size)
        return request.website.image_url(img_obj, 'image', size)

    @http.route([
        cfg_tmpl_url + '/image_update',
        cfg_step_url + '/image_update'
    ], type='json', auth='public', website=True)
    def image_update(self, product_tmpl, cfg_vals,
                     config_step=None, size=None):
        """ Method called via json from frontend to update the configuration image live
            before posting the data to the server

        :param product_tmpl: product.template object being configured
        :param cfg_vals: dictionary representing the client-side configuration
        :param size: string representing the image ratio e.g: '300x300'
        :returns: path to the selected image computed by get_config_image
        """
        # TODO: Verify if option is selectable with current configuration

        json_config = self.get_json_config(
            product_tmpl, cfg_vals, config_step)
        value_ids = product_tmpl.flatten_val_ids(
            json_config.get('attr_vals', {}).values())
        return self.get_config_image(product_tmpl, value_ids, size)

    def configure_product(self, product_tmpl, value_ids, custom_vals=None):
        """Method kept for backward compatiblity"""
        # TODO: Remove in next version
        if custom_vals is None:
            custom_vals = {}

        return product_tmpl.sudo().create_get_variant(value_ids, custom_vals)

    def get_attr_classes(self, attr_line, attr_value=False, custom=False):
        """Computes classes for attribute elements in frontend for the purpose
           of client-side validation and config image update

           :param attr_line: product.attribute.line object
           :param attr_value: product.attribute.value object
           :returns: string of classes to be added on the frontend element
        """
        # TODO: Make a mapper between oe_field_types and html input types
        product_tmpl = attr_line.product_tmpl_id

        cfg_img_lines = product_tmpl.config_image_ids
        img_vals = cfg_img_lines.mapped('value_ids')

        classes = []
        if attr_line.required:
            classes.append('required')

        if attr_value and not product_tmpl.values_available([attr_value.id]):
            classes.append('hidden')

        if custom:
            classes.append('custom_val')
            custom_type = attr_line.attribute_id.custom_type
            if custom_type == 'integer':
                classes.append('digits')
            elif custom_type == 'float':
                classes.append('number')
        elif img_vals & attr_line.value_ids:
            classes.append('cfg_img_update')
        return classes

    @http.route([cfg_tmpl_url, cfg_step_url], type='http',
                auth='public', website=True)
    def action_configure(
            self, product_tmpl, config_step=None, category='', **post):
        """ Controller called to parse the form of configurable products"""
        # TODO: Use a client-side session for the configuration values with a
        # expiration date set
        def _get_class_dependencies(value, dependencies):
            if value.id in dependencies:
                return' '.join(str(dep) for dep in dependencies[value.id])
            return False

        # category_obj = request.env['product.public.category']

        # if category:
        #     category = category_obj.browse(int(category))
            # category = category if category.exists() else False

        cfg_err = None
        fatal_error = None
        cfg_vars = self.config_vars(product_tmpl, active_step=config_step)

        post = self.parse_config_post(product_tmpl)

        if request.httprequest.method == 'POST':
            parsed_vals = self.config_parse(product_tmpl, post, config_step)
            if parsed_vals['errors']:
                cfg_err = parsed_vals['errors']
            else:
                self.config_update(
                    parsed_vals, cfg_session=cfg_vars['cfg_session'])

            if not cfg_vars.get('next_step') and not cfg_err:
                self.config_update(
                    parsed_vals, cfg_session=cfg_vars['cfg_session'])
                redirect = self.config_redirect(
                    product_tmpl, config_step, post,
                    cfg_vars['cfg_session'].value_ids.ids, {
                        x.attribute_id.id: x.value or x.attachment_ids for x in
                        cfg_vars['cfg_session'].custom_value_ids
                    })
                if redirect:
                    return redirect

                if cfg_vars['cfg_session'].sudo().action_confirm():
                    return self.product_redirect(cfg_vars['cfg_session'])
                else:
                    fatal_error = 'The configurator encountered a problem, '\
                                  'please try again later'

        redirect = self.config_redirect(
            product_tmpl, config_step, post,
            cfg_vars['cfg_session'].value_ids.ids, {
                x.attribute_id.id: x.value or x.attachment_ids for x in
                cfg_vars['cfg_session'].custom_value_ids
            })
        if redirect:
            return redirect

        pricelist = self.get_pricelist()

        keep = main.QueryURL(
            '/configurator', category=category and category.id)

        vals = {
            'json': json,
            # 'category': category,
            'product_tmpl': product_tmpl,
            'pricelist': pricelist,
            'get_class_dependencies': _get_class_dependencies,
            'get_attr_classes': self.get_attr_classes,
            'get_config_image': self.get_config_image,
            'cfg_err': cfg_err,
            'keep': keep,
            'fatal_error': fatal_error,
        }

        template_name = 'website_product_configurator.product_configurator'
        vals.update({'cfg_vars': cfg_vars})
        return request.render(template_name, vals)

    @http.route(
        '/configurator/config/<model("product.config.session"):cfg_session>',
        type='http', auth="public", website=True)
    def cfg_session(self, cfg_session, **post):
        try:
            product_tmpl = cfg_session.product_tmpl_id
        except:
            return request.redirect('/configurator')
        if post:
            custom_vals = {
                x.attribute_id.id: x.value or x.attachment_ids for x in
                cfg_session.custom_value_ids
            }
            product = cfg_session.product_tmpl_id.sudo().create_get_variant(
                cfg_session.value_ids.ids, custom_vals
            )
            cfg_session.sudo().unlink()
            return self.cart_update(product, post)

        def _get_product_vals(cfg_session):
            vals = [val for val in cfg_session.value_ids]
            vals += [val for val in cfg_session.custom_value_ids]
            return sorted(vals, key=lambda obj: obj.attribute_id.sequence)

        # product_obj = request.env['product.product'].with_context(
        #     active_id=product.id)

        pricelist = self.get_pricelist()

        keep = main.QueryURL('/configurator')

        # from_currency = request.env.user.with_context(
        #     active_id=product.id).company_id.currency_id
        # to_currency = pricelist.currency_id
        # compute_currency =
        # lambda price: request.env['res.currency']._compute(
        #     from_currency, to_currency, price)

        # if not request.env.context.get('pricelist'):
        #     product_obj = product_obj.with_context(pricelist=int(pricelist))
        # product = product_obj.browse(int(product))
        values = {
            'get_product_vals': _get_product_vals,
            'get_config_image': self.get_config_image,
            'product_tmpl': product_tmpl,
            # 'cfg_vars': self.config_vars(product.product_tmpl_id),
            # 'compute_currency': compute_currency,
            # 'main_object': product,
            'pricelist': pricelist,
            # 'product': product,
            'cfg_session': cfg_session,
            'keep': keep,
        }
        return request.render(
            "website_product_configurator.cfg_session", values)
        # TODO: If template not found redirect to product_configurator page

    def cart_update(self, product, post):
        request.website.sale_get_order(force_create=1)._cart_update(
            product_id=int(product.id),
            add_qty=float(post.get('add_qty')),
        )
        return request.redirect("/shop/cart")


class WebsiteSale(main.WebsiteSale):

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        """Redirect configurable products from webshop to configurator page
           """
        if product.config_ok:
            return request.redirect('/configurator/%s' % slug(product))
        return super(WebsiteSale, self).product(
            product=product, category=category, search=search, **kwargs)
