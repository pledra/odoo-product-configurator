# -*- coding: utf-8 -*-

from odoo.tools.misc import formatLang
from odoo.exceptions import ValidationError
from odoo import models, fields, api, tools, _
from lxml import etree


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    config_ok = fields.Boolean(string='Can be Configured')

    config_line_ids = fields.One2many(
        comodel_name='product.config.line',
        inverse_name='product_tmpl_id',
        string="Attribute Dependencies"
    )

    config_image_ids = fields.One2many(
        comodel_name='product.config.image',
        inverse_name='product_tmpl_id',
        string='Configuration Images'
    )

    config_step_line_ids = fields.One2many(
        comodel_name='product.config.step.line',
        inverse_name='product_tmpl_id',
        string='Configuration Lines'
    )

    def flatten_val_ids(self, value_ids):
        """ Return a list of value_ids from a list with a mix of ids
        and list of ids (multiselection)

        :param value_ids: list of value ids or mix of ids and list of ids
                           (e.g: [1, 2, 3, [4, 5, 6]])
        :returns: flattened list of ids ([1, 2, 3, 4, 5, 6]) """
        flat_val_ids = set()
        for val in value_ids:
            if not val:
                continue
            if isinstance(val, list):
                flat_val_ids |= set(val)
            elif isinstance(val, int):
                flat_val_ids.add(val)
        return list(flat_val_ids)

    def get_open_step_lines(self, value_ids):
        """
        Returns a recordset of configuration step lines open for access given
        the configuration passed through value_ids

        e.g: Field A and B from configuration step 2 depend on Field C
        from configuration step 1. Since fields A and B require action from
        the previous step, configuration step 2 is deemed closed and redirect
        is made for configuration step 1.

        :param value_ids: list of value.ids representing the
                          current configuration
        :returns: recordset of accesible configuration steps
        """

        open_step_lines = self.env['product.config.step.line']

        for cfg_line in self.config_step_line_ids:
            for attr_line in cfg_line.attribute_line_ids:
                available_vals = self.values_available(attr_line.value_ids.ids,
                                                       value_ids)
                # TODO: Refactor when adding restriction to custom values
                if available_vals or attr_line.custom:
                    open_step_lines |= cfg_line
                    break

        return open_step_lines.sorted()

    def get_adjacent_steps(self, value_ids, active_step_line_id=None):
        """Returns the previous and next steps given the configuration passed
        via value_ids and the active step line passed via cfg_step_line_id.

        If there is no open step return empty dictionary"""

        config_step_lines = self.config_step_line_ids

        if not config_step_lines:
            return {}

        active_cfg_step_line = config_step_lines.filtered(
            lambda l: l.id == active_step_line_id)

        open_step_lines = self.get_open_step_lines(value_ids)

        if not active_cfg_step_line:
            return {'next_step': open_step_lines[0]}

        nr_steps = len(open_step_lines)

        adjacent_steps = {}

        for i, cfg_step in enumerate(open_step_lines):
            if cfg_step == active_cfg_step_line:
                adjacent_steps.update({
                    'next_step':
                        None if i + 1 == nr_steps else open_step_lines[i + 1],
                    'previous_step': None if i == 0 else open_step_lines[i - 1]
                })
        return adjacent_steps

    def formatPrices(self, prices=None, dp='Product Price'):
        if prices is None:
            prices = {}
        dp = None
        prices['taxes'] = formatLang(
            self.env, prices['taxes'], monetary=True, dp=dp)
        prices['total'] = formatLang(
            self.env, prices['total'], monetary=True, dp=dp)
        prices['vals'] = [
            (v[0], v[1], formatLang(self.env, v[2], monetary=True, dp=dp))
            for v in prices['vals']
        ]
        return prices

    @api.multi
    def _get_option_values(self, value_ids, pricelist):
        """Return only attribute values that have products attached with a
        price set to them"""
        value_obj = self.env['product.attribute.value'].with_context({
            'pricelist': pricelist.id})
        values = value_obj.sudo().browse(value_ids).filtered(
            lambda x: x.product_id.price)
        return values

    @api.multi
    def get_components_prices(self, prices, value_ids,
                              custom_values, pricelist):
        """Return prices of the components which make up the final
        configured variant"""
        vals = self._get_option_values(value_ids, pricelist)
        for val in vals:
            prices['vals'].append(
                (val.attribute_id.name,
                 val.product_id.name,
                 val.product_id.price)
            )
            product = val.product_id.with_context({'pricelist': pricelist.id})
            product_prices = product.taxes_id.sudo().compute_all(
                price_unit=product.price,
                currency=pricelist.currency_id,
                quantity=1,
                product=self,
                partner=self.env.user.partner_id
            )

            total_included = product_prices['total_included']
            taxes = total_included - product_prices['total_excluded']
            prices['taxes'] += taxes
            prices['total'] += total_included
        return prices

    @api.multi
    def get_cfg_price(self, value_ids, custom_values=None,
                      pricelist_id=None, formatLang=False):
        """ Computes the price of the configured product based on the configuration
            passed in via value_ids and custom_values

        :param value_ids: list of attribute value_ids
        :param custom_values: dictionary of custom attribute values
        :param pricelist_id: id of pricelist to use for price computation
        :param formatLang: boolean for formatting price dictionary
        :returns: dictionary of prices per attribute and total price"""
        self.ensure_one()
        if custom_values is None:
            custom_values = {}
        if not pricelist_id:
            pricelist = self.env.user.partner_id.property_product_pricelist
            pricelist_id = pricelist.id
        else:
            pricelist = self.env['product.pricelist'].browse(pricelist_id)

        currency = pricelist.currency_id

        product = self.with_context({'pricelist': pricelist.id})

        base_prices = product.taxes_id.sudo().compute_all(
            price_unit=product.price,
            currency=pricelist.currency_id,
            quantity=1,
            product=product,
            partner=self.env.user.partner_id
        )

        total_included = base_prices['total_included']
        total_excluded = base_prices['total_excluded']

        prices = {
            'vals': [
                ('Base', self.name, total_excluded)
            ],
            'total': total_included,
            'taxes': total_included - total_excluded,
            'currency': currency.name
        }

        component_prices = self.get_components_prices(
            prices, value_ids, custom_values, pricelist)
        prices.update(component_prices)

        if formatLang:
            return self.formatPrices(prices)
        return prices

    @api.multi
    def search_variant(self, value_ids, custom_values=None):
        """ Searches product.variants with given value_ids and custom values
            given in the custom_values dict

            :param value_ids: list of product.attribute.values ids
            :param custom_values: dict {product.attribute.id: custom_value}

            :returns: product.product recordset of products matching domain
        """
        self.ensure_one()

        if custom_values is None:
            custom_values = {}
        attr_obj = self.env['product.attribute']

        domain = [('product_tmpl_id', '=', self.id)]

        for value_id in value_ids:
            domain.append(('attribute_value_ids', '=', value_id))

        attr_search = attr_obj.search([
            ('search_ok', '=', True),
            ('custom_type', 'not in', attr_obj._get_nosearch_fields())
        ])

        for attr_id, value in custom_values.iteritems():
            if attr_id not in attr_search.ids:
                domain.append(
                    ('value_custom_ids.attribute_id', '!=', int(attr_id)))
            else:
                domain.append(
                    ('value_custom_ids.attribute_id', '=', int(attr_id)))
                domain.append(('value_custom_ids.value', '=', value))

        products = self.env['product.product'].search(domain)

        # At this point, we might have found products with all of the passed
        # in values, but it might have more attributes!  These are NOT
        # matches
        more_attrs = products.filtered(
            lambda p:
            len(p.attribute_value_ids) != len(value_ids) or
            len(p.value_custom_ids) != len(custom_values)
            )
        products -= more_attrs
        return products

    def get_config_image_obj(self, value_ids, size=None):
        """
        Retreive the image object that most closely resembles the configuration
        code sent via value_ids list

        The default image object is the template (self)
        :param value_ids: a list representing the ids of attribute values
                         (usually stored in the user's session)
        :returns: path to the selected image
        """
        # TODO: Also consider custom values for image change
        img_obj = self
        max_matches = 0
        value_ids = self.flatten_val_ids(value_ids)
        for line in self.config_image_ids:
            matches = len(set(line.value_ids.ids) & set(value_ids))
            if matches > max_matches:
                img_obj = line
                max_matches = matches
        return img_obj

    @api.multi
    def encode_custom_values(self, custom_values):
        """ Hook to alter the values of the custom values before creating or writing

            :param custom_values: dict {product.attribute.id: custom_value}

            :returns: list of custom values compatible with write and create
        """
        attr_obj = self.env['product.attribute']
        binary_attribute_ids = attr_obj.search([
            ('custom_type', '=', 'binary')]).ids

        custom_lines = []

        for key, val in custom_values.iteritems():
            custom_vals = {'attribute_id': key}
            # TODO: Is this extra check neccesairy as we already make
            # the check in validate_configuration?
            attr_obj.browse(key).validate_custom_val(val)
            if key in binary_attribute_ids:
                custom_vals.update({
                    'attachment_ids': [(6, 0, val.ids)]
                })
            else:
                custom_vals.update({'value': val})
            custom_lines.append((0, 0, custom_vals))
        return custom_lines

    @api.multi
    def get_variant_vals(self, value_ids, custom_values=None, **kwargs):
        """ Hook to alter the values of the product variant before creation

            :param value_ids: list of product.attribute.values ids
            :param custom_values: dict {product.attribute.id: custom_value}

            :returns: dictionary of values to pass to product.create() method
         """
        self.ensure_one()

        image = self.get_config_image_obj(value_ids).image
        all_images = tools.image_get_resized_images(
            image, avoid_resize_medium=True)
        vals = {
            'product_tmpl_id': self.id,
            'attribute_value_ids': [(6, 0, value_ids)],
            'taxes_id': [(6, 0, self.taxes_id.ids)],
            'image': image,
            'image_variant': image,
            'image_medium': all_images['image_medium'],
            'image_small': all_images['image_medium'],
        }

        if custom_values:
            vals.update({
                'value_custom_ids': self.encode_custom_values(custom_values)
            })

        return vals

    @api.multi
    def create_variant(self, value_ids, custom_values=None):
        """Wrapper method for backward compatibility"""
        # TODO: Remove in newer versions
        return self.create_get_variant(
            value_ids=value_ids, custom_values=custom_values)

    @api.multi
    def create_get_variant(self, value_ids, custom_values=None):
        """ Creates a new product variant with the attributes passed via value_ids
        and custom_values or retrieves an existing one based on search result

            :param value_ids: list of product.attribute.values ids
            :param custom_values: dict {product.attribute.id: custom_value}

            :returns: new/existing product.product recordset

        """
        if custom_values is None:
            custom_values = {}
        valid = self.validate_configuration(value_ids, custom_values)
        if not valid:
            raise ValidationError(_('Invalid Configuration'))

        duplicates = self.search_variant(value_ids,
                                         custom_values=custom_values)

        # At the moment, I don't have enough confidence with my understanding
        # of binary attributes, so will leave these as not matching...
        # In theory, they should just work, if they are set to "non search"
        # in custom field def!
        # TODO: Check the logic with binary attributes
        if custom_values:
            value_custom_ids = self.encode_custom_values(custom_values)
            if any('attachment_ids' in cv[2] for cv in value_custom_ids):
                duplicates = False

        if duplicates:
            return duplicates[0]

        vals = self.get_variant_vals(value_ids, custom_values)
        variant = self.env['product.product'].create(vals)

        return variant

    def validate_domains_against_sels(self, domains, sel_val_ids):
        # process domains as shown in this wikipedia pseudocode:
        # https://en.wikipedia.org/wiki/Polish_notation#Order_of_operations
        stack = []
        for domain in reversed(domains):
            if type(domain) == tuple:
                # evaluate operand and push to stack
                if domain[1] == 'in':
                    if not set(domain[2]) & set(sel_val_ids):
                        stack.append(False)
                        continue
                else:
                    if set(domain[2]) & set(sel_val_ids):
                        stack.append(False)
                        continue
                stack.append(True)
            else:
                # evaluate operator and previous 2 operands
                # compute_domain() only inserts 'or' operators
                # compute_domain() enforces 2 operands per operator
                operand1 = stack.pop()
                operand2 = stack.pop()
                stack.append(operand1 or operand2)

        # 'and' operator is implied for remaining stack elements
        avail = True
        while stack:
            avail &= stack.pop()
        return avail

    @api.multi
    def values_available(self, attr_val_ids, sel_val_ids):
        """Determines whether the attr_values from the product_template
        are available for selection given the configuration ids and the
        dependencies set on the product template

        :param attr_val_ids: list of attribute value ids to check for
                             availability
        :param sel_val_ids: list of attribute value ids already selected

        :returns: list of available attribute values
        """

        avail_val_ids = []
        for attr_val_id in attr_val_ids:

            config_lines = self.config_line_ids.filtered(
                lambda l: attr_val_id in l.value_ids.ids
            )
            domains = config_lines.mapped('domain_id').compute_domain()

            avail = self.validate_domains_against_sels(domains, sel_val_ids)
            if avail:
                avail_val_ids.append(attr_val_id)

        return avail_val_ids

    @api.multi
    def validate_configuration(self, value_ids, custom_vals=None, final=True):
        """ Verifies if the configuration values passed via value_ids and custom_vals
        are valid

        :param value_ids: list of attribute value ids
        :param custom_vals: custom values dict {attr_id: custom_val}
        :param final: boolean marker to check required attributes.
                      pass false to check non-final configurations

        :returns: Error dict with reason of validation failure
                  or True
        """
        # TODO: Raise ConfigurationError with reason
        # Check if required values are missing for final configuration
        if custom_vals is None:
            custom_vals = {}

        for line in self.attribute_line_ids:
            # Validate custom values
            attr = line.attribute_id
            if attr.id in custom_vals:
                attr.validate_custom_val(custom_vals[attr.id])
            if final:
                common_vals = set(value_ids) & set(line.value_ids.ids)
                custom_val = custom_vals.get(attr.id)
                if line.required and not common_vals and not custom_val:
                    # TODO: Verify custom value type to be correct
                    return False

        # Check if all all the values passed are not restricted
        avail_val_ids = self.values_available(value_ids, value_ids)
        if set(value_ids) - set(avail_val_ids):
            return False

        # Check if custom values are allowed
        custom_attr_ids = self.attribute_line_ids.filtered(
            'custom').mapped('attribute_id').ids

        if not set(custom_vals.keys()) <= set(custom_attr_ids):
            return False

        # Check if there are multiple values passed for non-multi attributes
        mono_attr_lines = self.attribute_line_ids.filtered(
            lambda l: not l.multi)

        for line in mono_attr_lines:
            if len(set(line.value_ids.ids) & set(value_ids)) > 1:
                return False
        return True

    @api.multi
    def toggle_config(self):
        for record in self:
            record.config_ok = not record.config_ok

    # Override name_search delegation to variants introduced by Odony
    # TODO: Verify this is still a problem in v9
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        return super(models.Model, self).name_search(name=name,
                                                     args=args,
                                                     operator=operator,
                                                     limit=limit)

    @api.multi
    def create_variant_ids(self):
        """ Prevent configurable products from creating variants as these serve
            only as a template for the product configurator"""
        templates = self.filtered(lambda t: not t.config_ok)
        if not templates:
            return None
        return super(ProductTemplate, templates).create_variant_ids()

    @api.multi
    def unlink(self):
        """ Prevent the removal of configurable product templates
            from variants"""
        for template in self:
            variant_unlink = self.env.context.get('unlink_from_variant', False)
            if template.config_ok and variant_unlink:
                self -= template
        res = super(ProductTemplate, self).unlink()
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _rec_name = 'config_name'

    def _get_conversions_dict(self):
        conversions = {
            'float': float,
            'int': int
        }
        return conversions

    @api.multi
    @api.constrains('attribute_value_ids')
    def _check_duplicate_product(self):
        if not self.config_ok:
            return None

        # At the moment, I don't have enough confidence with my understanding
        # of binary attributes, so will leave these as not matching...
        # In theory, they should just work, if they are set to "non search"
        # in custom field def!
        # TODO: Check the logic with binary attributes
        if self.value_custom_ids.filtered(lambda cv: cv.attachment_ids):
            pass
        else:
            custom_values = {
                cv.attribute_id.id: cv.value
                for cv in self.value_custom_ids
                }

            duplicates = self.product_tmpl_id.search_variant(
                self.attribute_value_ids.ids,
                custom_values=custom_values
                ).filtered(lambda p: p.id != self.id)

            if duplicates:
                raise ValidationError(
                    _("Configurable Products cannot have duplicates "
                      "(identical attribute values)")
                )

    @api.multi
    def _compute_product_price_extra(self):
        """Compute price of configurable products as sum
        of products related to attribute values picked"""
        products = self.filtered(lambda x: not x.config_ok)
        configurable_products = self - products
        if products:
            prices = super(ProductProduct, self)._compute_product_price_extra()

        conversions = self._get_conversions_dict()
        for product in configurable_products:
            lst_price = product.product_tmpl_id.lst_price
            value_ids = product.attribute_value_ids.ids
            # TODO: Merge custom values from products with cfg session
            # and use same method to retrieve parsed custom val dict
            custom_vals = {}
            for val in product.value_custom_ids:
                custom_type = val.attribute_id.custom_type
                if custom_type in conversions:
                    try:
                        custom_vals[val.attribute_id.id] = conversions[
                            custom_type](val.value)
                    except:
                        raise ValidationError(
                            _("Could not convert custom value '%s' to '%s' on "
                              "product variant: '%s'" % (val.value,
                                                         custom_type,
                                                         product.display_name))
                        )
                else:
                    custom_vals[val.attribute_id.id] = val.value
            prices = product.product_tmpl_id.get_cfg_price(
                value_ids, custom_vals)
            product.price_extra = prices['total'] - prices['taxes'] - lst_price

    config_name = fields.Char(
        string="Name",
        size=256,
        compute='_compute_name',
    )
    value_custom_ids = fields.One2many(
        comodel_name='product.attribute.value.custom',
        inverse_name='product_id',
        string='Custom Values',
        readonly=True
    )

    @api.multi
    def _check_attribute_value_ids(self):
        """ Removing multi contraint attribute to enable multi selection. """
        return True

    _constraints = [
        (_check_attribute_value_ids, None, ['attribute_value_ids'])
    ]

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ For configurable products switch the name field with the config_name
            so as to keep the view intact in whatever form it is at the moment
            of execution and not duplicate the original just for the sole
            purpose of displaying the proper name"""
        res = super(ProductProduct, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu
        )
        if self.env.context.get('default_config_ok'):
            xml_view = etree.fromstring(res['arch'])
            xml_name = xml_view.xpath("//field[@name='name']")
            xml_label = xml_view.xpath("//label[@for='name']")
            if xml_name:
                xml_name[0].attrib['name'] = 'config_name'
                if xml_label:
                    xml_label[0].attrib['for'] = 'config_name'
                view_obj = self.env['ir.ui.view']
                xarch, xfields = view_obj.postprocess_and_fields(self._name,
                                                                 xml_view,
                                                                 view_id)
                res['arch'] = xarch
                res['fields'] = xfields
        return res

    # TODO: Implement naming method for configured products
    # TODO: Provide a field with custom name in it that defaults to a name
    # pattern
    def get_config_name(self):
        return self.name

    @api.multi
    def unlink(self):
        """ Signal unlink from product variant through context so
            removal can be stopped for configurable templates """
        ctx = dict(self.env.context, unlink_from_variant=True)
        self.env.context = ctx
        return super(ProductProduct, self).unlink()

    @api.multi
    def _compute_name(self):
        """ Compute the name of the configurable products and use template
            name for others"""
        for product in self:
            if product.config_ok:
                product.config_name = product.get_config_name()
            else:
                product.config_name = product.name
