from ast import literal_eval

from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, ValidationError
from odoo.tools.misc import formatLang


class ProductConfigDomain(models.Model):
    _name = 'product.config.domain'

    @api.multi
    @api.depends('implied_ids')
    def _get_trans_implied(self):
        "Computes the transitive closure of relation implied_ids"

        def linearize(domains):
            trans_domains = domains
            for domain in domains:
                implied_domains = domain.implied_ids - domain
                if implied_domains:
                    trans_domains |= linearize(implied_domains)
            return trans_domains

        for domain in self:
            domain.trans_implied_ids = linearize(domain)

    @api.multi
    def compute_domain(self):
        """ Returns a list of domains defined on a product.config.domain_line_ids
            and all implied_ids"""
        # TODO: Enable the usage of OR operators between implied_ids
        # TODO: Add implied_ids sequence field to enforce order of operations
        # TODO: Prevent circular dependencies
        computed_domain = []
        for domain in self:
            lines = domain.trans_implied_ids.mapped('domain_line_ids').sorted()
            for line in lines[:-1]:
                if line.operator == 'or':
                    computed_domain.append('|')
                computed_domain.append(
                    (line.attribute_id.id,
                     line.condition,
                     line.value_ids.ids)
                )
            # ensure 2 operands follow the last operator
            computed_domain.append(
                (lines[-1].attribute_id.id,
                 lines[-1].condition,
                 lines[-1].value_ids.ids)
            )
        return computed_domain

    name = fields.Char(
        string='Name',
        required=True,
        size=256
    )
    domain_line_ids = fields.One2many(
        comodel_name='product.config.domain.line',
        inverse_name='domain_id',
        string='Restrictions',
        required=True
    )
    implied_ids = fields.Many2many(
        comodel_name='product.config.domain',
        relation='product_config_domain_implied_rel',
        string='Inherited',
        column1='domain_id',
        column2='parent_id'
    )
    trans_implied_ids = fields.Many2many(
        comodel_name='product.config.domain',
        compute=_get_trans_implied,
        column1='domain_id',
        column2='parent_id',
        string='Transitively inherits'
    )


class ProductConfigDomainLine(models.Model):
    _name = 'product.config.domain.line'
    _order = 'sequence'

    def _get_domain_conditions(self):
        operators = [
            ('in', 'In'),
            ('not in', 'Not In')
        ]

        return operators

    def _get_domain_operators(self):
        andor = [
            ('and', 'And'),
            ('or', 'Or'),
        ]

        return andor

    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True)

    domain_id = fields.Many2one(
        comodel_name='product.config.domain',
        required=True,
        string='Rule')

    condition = fields.Selection(
        selection=_get_domain_conditions,
        string="Condition",
        required=True)

    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        relation='product_config_domain_line_attr_rel',
        column1='line_id',
        column2='attribute_id',
        string='Values',
        required=True
    )

    operator = fields.Selection(
        selection=_get_domain_operators,
        string='Operators',
        default='and',
        required=True
    )

    sequence = fields.Integer(
        string="Sequence",
        default=1,
        help="Set the order of operations for evaluation domain lines"
    )


class ProductConfigLine(models.Model):
    _name = 'product.config.line'

    # TODO: Prevent config lines having dependencies that are not set in other
    # config lines
    # TODO: Prevent circular depdencies: Length -> Color, Color -> Length

    @api.onchange('attribute_line_id')
    def onchange_attribute(self):
        self.value_ids = False
        self.domain_id = False

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        ondelete='cascade',
        required=True
    )

    attribute_line_id = fields.Many2one(
        comodel_name='product.attribute.line',
        string='Attribute Line',
        ondelete='cascade',
        required=True
    )

    # TODO: Find a more elegant way to restrict the value_ids
    attr_line_val_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        related='attribute_line_id.value_ids'
    )

    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        id1="cfg_line_id",
        id2="attr_val_id",
        string="Values"
    )

    domain_id = fields.Many2one(
        comodel_name='product.config.domain',
        required=True,
        string='Restrictions'
    )

    sequence = fields.Integer(string='Sequence', default=10)

    _order = 'product_tmpl_id, sequence, id'

    @api.multi
    @api.constrains('value_ids')
    def check_value_attributes(self):
        for line in self:
            value_attributes = line.value_ids.mapped('attribute_id')
            if value_attributes != line.attribute_line_id.attribute_id:
                raise ValidationError(
                    _("Values must belong to the attribute of the "
                      "corresponding attribute_line set on the configuration "
                      "line")
                )


class ProductConfigImage(models.Model):
    _name = 'product.config.image'

    name = fields.Char('Name', size=128, required=True, translate=True)

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        ondelete='cascade',
        required=True
    )

    image = fields.Binary('Image', required=True)

    sequence = fields.Integer(string='Sequence', default=10)

    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        string='Configuration'
    )

    _order = 'sequence'

    @api.multi
    @api.constrains('value_ids')
    def _check_value_ids(self):
        cfg_session_obj = self.env['product.config.session']
        for cfg_img in self:
            valid = cfg_session_obj.validate_configuration(
                value_ids=cfg_img.value_ids.ids, final=False)
            if not valid:
                raise ValidationError(
                    _("Values entered for line '%s' generate "
                      "a incompatible configuration" % cfg_img.name)
                )


class ProductConfigStep(models.Model):
    _name = 'product.config.step'

    # TODO: Prevent values which have dependencies to be set in a
    #       step with higher sequence than the dependency

    name = fields.Char(
        string='Name',
        size=128,
        required=True,
        translate=True
    )


class ProductConfigStepLine(models.Model):
    _name = 'product.config.step.line'

    name = fields.Char(related='config_step_id.name')

    config_step_id = fields.Many2one(
        comodel_name='product.config.step',
        string='Configuration Step',
        required=True
    )
    attribute_line_ids = fields.Many2many(
        comodel_name='product.attribute.line',
        relation='config_step_line_attr_id_rel',
        column1='cfg_line_id',
        column2='attr_id',
        string='Attribute Lines'
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template',
        ondelete='cascade',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    _order = 'sequence, config_step_id, id'

    @api.constrains('config_step_id')
    def _check_config_step(self):
        cfg_step_lines = self.product_tmpl_id.config_step_line_ids
        cfg_steps = cfg_step_lines.filtered(
            lambda line: line != self).mapped('config_step_id')
        if self.config_step_id in cfg_steps:
            raise Warning(_('Cannot have a configuration step defined twice.'))


class ProductConfigSession(models.Model):
    _name = 'product.config.session'

    @api.multi
    @api.depends('value_ids')
    def _compute_cfg_price(self):
        for session in self:
            if session.product_tmpl_id:
                price = session.get_cfg_price()['total']
            else:
                price = 0.00
            session.price = price

    @api.model
    def _get_custom_vals_dict(self):
        """Retrieve session custom values as a dictionary of the form
           {attribute_id: parsed_custom_value}"""
        custom_vals = {}
        for val in self.custom_value_ids:
            if val.attribute_id.custom_type in ['float', 'int']:
                custom_vals[val.attribute_id.id] = literal_eval(val.value)
            elif val.attribute_id.custom_type == 'binary':
                custom_vals[val.attribute_id.id] = val.attachment_ids
            else:
                custom_vals[val.attribute_id.id] = val.value
        return custom_vals

    @api.multi
    def _get_config_step_name(self):
        """Get the config.step.line name using the string stored in config_step
         field of the session"""
        cfg_step_line_obj = self.env['product.config.step.line']
        cfg_session_step_lines = self.mapped('config_step')
        cfg_step_line_ids = set()
        for step in cfg_session_step_lines:
            try:
                cfg_step_line_ids.add(int(step))
            except ValueError:
                pass
        cfg_step_lines = cfg_step_line_obj.browse(cfg_step_line_ids)
        for session in self:
            try:
                config_step = int(session.config_step)
                config_step_line = cfg_step_lines.filtered(
                    lambda x: x.id == config_step
                )
                session.config_step_name = config_step_line.name
            except Exception:
                pass
            if not session.config_step_name:
                session.config_step_name = session.config_step

    name = fields.Char(
        string='Configuration Session Number',
        readonly=True
    )
    config_step = fields.Char(
        string='Configuration Step ID'
    )
    config_step_name = fields.Char(
        compute='_get_config_step_name',
        string="Configuration Step"
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        domain=[('config_ok', '=', True)],
        string='Configurable Template',
        required=True
    )
    value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        relation='product_config_session_attr_values_rel',
        column1='cfg_session_id',
        column2='attr_val_id',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        required=True,
        string='User'
    )
    custom_value_ids = fields.One2many(
        comodel_name='product.config.session.custom.value',
        inverse_name='cfg_session_id',
        string='Custom Values'
    )
    price = fields.Float(
        compute='_compute_cfg_price',
        string='Price',
        store=True,
    )
    state = fields.Selection(
        string='State',
        required=True,
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done')
        ],
        default='draft'
    )

    @api.multi
    def action_confirm(self):
        if self.product_tmpl_id.config_ok:
            valid = self.validate_configuration()
            if not valid:
                return valid
        self.state = 'done'
        return True

    @api.multi
    def update_config(self, attr_val_dict=None, custom_val_dict=None):
        """Update the session object with the given value_ids and custom values.

        Use this method instead of write in order to prevent incompatible
        configurations as this removed duplicate values for the same attribute.

        :param attr_val_dict: Dictionary of the form {
            int (attribute_id): attribute_value_id OR [attribute_value_ids]
        }

        :custom_val_dict: Dictionary of the form {
            int (attribute_id): {
                'value': 'custom val',
                OR
                'attachment_ids': {
                    [{
                        'name': 'attachment name',
                        'datas': base64_encoded_string
                    }]
                }
            }
        }

        """
        if attr_val_dict is None:
            attr_val_dict = {}
        if custom_val_dict is None:
            custom_val_dict = {}
        update_vals = {}

        value_ids = self.value_ids.ids
        for attr_id, vals in attr_val_dict.items():
            attr_val_ids = self.value_ids.filtered(
                lambda x: x.attribute_id.id == int(attr_id)).ids
            # Remove all values for this attribute and add vals from dict
            value_ids = list(set(value_ids) - set(attr_val_ids))
            if not vals:
                continue
            if isinstance(vals, list):
                value_ids += vals
            elif isinstance(vals, int):
                value_ids.append(vals)

        if value_ids != self.value_ids.ids:
            update_vals.update({
                'value_ids': [(6, 0, value_ids)]
            })

        # Remove all custom values included in the custom_vals dict
        self.custom_value_ids.filtered(
            lambda x: x.attribute_id.id in custom_val_dict.keys()).unlink()

        if custom_val_dict:
            binary_field_ids = self.env['product.attribute'].search([
                ('id', 'in', list(custom_val_dict.keys())),
                ('custom_type', '=', 'binary')
            ]).ids
        for attr_id, vals in custom_val_dict.items():
            if not vals:
                continue

            if 'custom_value_ids' not in update_vals:
                update_vals['custom_value_ids'] = []

            custom_vals = {'attribute_id': attr_id}

            if attr_id in binary_field_ids:
                attachments = [(0, 0, {
                    'name': val.get('name'),
                    'datas_fname': val.get('name'),
                    'datas': val.get('datas')
                }) for val in vals]
                custom_vals.update({'attachment_ids': attachments})
            else:
                custom_vals.update({'value': vals})

            update_vals['custom_value_ids'].append((0, 0, custom_vals))
        self.write(update_vals)

    @api.multi
    def write(self, vals):
        """Validate configuration when writing new values to session"""
        # TODO: Issue warning when writing to value_ids or custom_val_ids
        res = super(ProductConfigSession, self).write(vals)
        value_ids = self.value_ids.ids
        avail_val_ids = self.values_available(value_ids)
        if set(value_ids) - set(avail_val_ids):
            self.value_ids = [(6, 0, avail_val_ids)]
        valid = self.validate_configuration(final=False)
        if not valid:
            raise ValidationError(_('Invalid Configuration'))
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'product.config.session') or _('New')
        product_tmpl = self.env['product.template'].browse(
            vals.get('product_tmpl_id')).exists()
        if product_tmpl:
            default_val_ids = product_tmpl.attribute_line_ids.filtered(
                lambda l: l.default_val).mapped('default_val').ids
            value_ids = vals.get('value_ids')
            if value_ids:
                default_val_ids += value_ids[0][2]
            valid_conf = self.validate_configuration(
                value_ids=default_val_ids, final=False)
            # TODO: Remove if cond when PR with raise error on github is merged
            if not valid_conf:
                raise ValidationError(
                    _('Default values provided generate an invalid '
                      'configuration')
                )
            vals.update({'value_ids': [(6, 0, default_val_ids)]})
        return super(ProductConfigSession, self).create(vals)

    @api.multi
    def create_get_variant(self, value_ids=None, custom_vals=None):
        """ Creates a new product variant with the attributes passed via value_ids
        and custom_values or retrieves an existing one based on search result

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: new/existing product.product recordset

        """
        if not value_ids:
            value_ids = self.value_ids.ids

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        valid = self.validate_configuration()
        if not valid:
            raise ValidationError(_('Invalid Configuration'))

        duplicates = self.search_variant(
            value_ids=value_ids, custom_vals=custom_vals)

        # At the moment, I don't have enough confidence with my understanding
        # of binary attributes, so will leave these as not matching...
        # In theory, they should just work, if they are set to "non search"
        # in custom field def!
        # TODO: Check the logic with binary attributes
        if custom_vals:
            value_custom_ids = self.encode_custom_values(custom_vals)
            if any('attachment_ids' in cv[2] for cv in value_custom_ids):
                duplicates = False

        if duplicates:
            self.action_confirm()
            return duplicates[:1]

        vals = self.get_variant_vals(value_ids, custom_vals)
        variant = self.env['product.product'].create(vals)

        # TODO: Find a better way to locate the session (could be subsession)

        self.action_confirm()

        return variant

    @api.multi
    def _get_option_values(self, pricelist, value_ids=None):
        """Return only attribute values that have products attached with a
        price set to them"""
        if not value_ids:
            value_ids = self.value_ids.ids

        value_obj = self.env['product.attribute.value'].with_context({
            'pricelist': pricelist.id})
        values = value_obj.sudo().browse(value_ids).filtered(
            lambda x: x.product_id.price)
        return values

    @api.multi
    def get_components_prices(self, prices, pricelist, value_ids=None):
        """Return prices of the components which make up the final
        configured variant"""

        if not value_ids:
            value_ids = self.value_ids.ids

        vals = self._get_option_values(pricelist, value_ids)
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

    @api.model
    def get_cfg_price(self, value_ids=None, custom_vals=None,
                      pricelist_id=None, formatLang=False):
        """ Computes the price of the configured product based on the configuration
            passed in via value_ids and custom_values

        :param value_ids: list of attribute value_ids
        :param custom_vals: dictionary of custom attribute values
        :param pricelist_id: id of pricelist to use for price computation
        :param formatLang: boolean for formatting price dictionary
        :returns: dictionary of prices per attribute and total price"""

        if not value_ids:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = {}

        if not pricelist_id:
            pricelist = self.env.user.partner_id.property_product_pricelist
            pricelist_id = pricelist.id
        else:
            pricelist = self.env['product.pricelist'].browse(pricelist_id)

        currency = pricelist.currency_id

        product = self.product_tmpl_id.with_context({
            'pricelist': pricelist.id
        })

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
                ('Base', self.product_tmpl_id.name, total_excluded)
            ],
            'total': total_included,
            'taxes': total_included - total_excluded,
            'currency': currency.name
        }

        component_prices = self.get_components_prices(
            prices, pricelist, value_ids
        )
        prices.update(component_prices)

        if formatLang:
            return self.formatPrices(prices)
        return prices

    def get_config_image(
            self, value_ids=None, custom_vals=None, size=None):
        """
        Retreive the image object that most closely resembles the configuration
        code sent via value_ids list

        The default image object is the template (self)
        :param value_ids: a list representing the ids of attribute values
                         (usually stored in the user's session)
        :param custom_vals: dictionary of custom attribute values
        :returns: path to the selected image
        """
        # TODO: Also consider custom values for image change
        if not value_ids:
            value_ids = self.value_ids.ids

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        img_obj = self.product_tmpl_id
        max_matches = 0
        value_ids = self.flatten_val_ids(value_ids)
        for line in self.product_tmpl_id.config_image_ids:
            matches = len(set(line.value_ids.ids) & set(value_ids))
            if matches > max_matches:
                img_obj = line
                max_matches = matches
        return img_obj.image

    @api.model
    def get_variant_vals(self, value_ids=None, custom_vals=None, **kwargs):
        """ Hook to alter the values of the product variant before creation

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: dictionary of values to pass to product.create() method
         """
        self.ensure_one()

        if not value_ids:
            value_ids = self.value_ids.ids

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        image = self.get_config_image(value_ids)
        all_images = tools.image_get_resized_images(
            image, avoid_resize_medium=True)
        vals = {
            'product_tmpl_id': self.product_tmpl_id.id,
            'attribute_value_ids': [(6, 0, value_ids)],
            'taxes_id': [(6, 0, self.product_tmpl_id.taxes_id.ids)],
            'image': image,
            'image_variant': image,
            'image_medium': all_images['image_medium'],
            'image_small': all_images['image_medium'],
        }

        if custom_vals:
            vals.update({
                'value_custom_ids': self.encode_custom_values(custom_vals)
            })
        return vals

    @api.multi
    def get_session_search_domain(self, product_tmpl_id, state='draft',
                                  parent_id=None):
        domain = [
            ('product_tmpl_id', '=', product_tmpl_id),
            ('user_id', '=', self.env.uid),
            ('state', '=', state),
        ]
        if parent_id:
            domain.append(('parent_id', '=', parent_id))
        return domain

    @api.multi
    def get_session_vals(self, product_tmpl_id, parent_id=None):
        vals = {
            'product_tmpl_id': product_tmpl_id,
            'user_id': self.env.user.id,
        }
        if parent_id:
            vals.update(parent_id=parent_id)
        return vals

    @api.model
    def get_active_step(self):
        """Attempt to return product.config.step.line object that has the id
        of the config session step stored as string"""
        cfg_step_line_obj = self.env['product.config.step.line']

        try:
            cfg_step_line_id = int(self.config_step)
        except ValueError:
            cfg_step_line_id = None

        if cfg_step_line_id:
            return cfg_step_line_obj.browse(cfg_step_line_id)
        return cfg_step_line_obj

    @api.model
    def get_open_step_lines(self, value_ids=None):
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

        if not value_ids:
            value_ids = self.value_ids.ids

        open_step_lines = self.env['product.config.step.line']

        for cfg_line in self.product_tmpl_id.config_step_line_ids:
            for attr_line in cfg_line.attribute_line_ids:
                available_vals = self.values_available(
                    attr_line.value_ids.ids, value_ids
                )
                # TODO: Refactor when adding restriction to custom values
                if available_vals or attr_line.custom:
                    open_step_lines |= cfg_line
                    break

        return open_step_lines.sorted()

    @api.model
    def get_adjacent_steps(self, value_ids=None, active_step_line_id=None):
        """Returns the previous and next steps given the configuration passed
        via value_ids and the active step line passed via cfg_step_line_id."""

        # If there is no open step return empty dictionary

        if not value_ids:
            value_ids = self.value_ids.ids

        if not active_step_line_id:
            active_step_line_id = self.get_active_step().id

        config_step_lines = self.product_tmpl_id.config_step_line_ids

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

    @api.model
    def get_variant_search_domain(
            self, product_tmpl_id=None, value_ids=None, custom_vals=None):
        """Method called by search_variant used to search duplicates in the
        database"""

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        if not value_ids:
            value_ids = self.value_ids.ids

        attr_obj = self.env['product.attribute']

        domain = [
            ('product_tmpl_id', '=', product_tmpl_id),
            ('config_ok', '=', True)
        ]

        for value_id in value_ids:
            domain.append(('attribute_value_ids', '=', value_id))

        attr_search = attr_obj.search([
            ('search_ok', '=', True),
            ('custom_type', 'not in', attr_obj._get_nosearch_fields())
        ])

        for attr_id, value in custom_vals.items():
            if attr_id not in attr_search.ids:
                domain.append(
                    ('value_custom_ids.attribute_id', '!=', int(attr_id)))
            else:
                domain.append(
                    ('value_custom_ids.attribute_id', '=', int(attr_id)))
                domain.append(('value_custom_ids.value', '=', value))
        return domain

    def validate_domains_against_sels(
            self, domains, value_ids=None, custom_vals=None):

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        if not value_ids:
            value_ids = self.value_ids.ids

        # process domains as shown in this wikipedia pseudocode:
        # https://en.wikipedia.org/wiki/Polish_notation#Order_of_operations
        stack = []
        for domain in reversed(domains):
            if type(domain) == tuple:
                # evaluate operand and push to stack
                if domain[1] == 'in':
                    if not set(domain[2]) & set(value_ids):
                        stack.append(False)
                        continue
                else:
                    if set(domain[2]) & set(value_ids):
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

    @api.model
    def values_available(
            self, check_val_ids, value_ids=None, custom_vals=None):
        """Determines whether the attr_values from the product_template
        are available for selection given the configuration ids and the
        dependencies set on the product template

        :param check_val_ids: list of attribute value ids to check for
                              availability
        :param value_ids: list of attribute value ids
        :param custom_vals: custom values dict {attr_id: custom_val}

        :returns: list of available attribute values
        """

        if not value_ids:
            value_ids = self.value_ids.ids

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        avail_val_ids = []
        for attr_val_id in check_val_ids:

            config_lines = self.product_tmpl_id.config_line_ids.filtered(
                lambda l: attr_val_id in l.value_ids.ids
            )
            domains = config_lines.mapped('domain_id').compute_domain()

            avail = self.validate_domains_against_sels(
                domains, value_ids, custom_vals
            )
            if avail:
                avail_val_ids.append(attr_val_id)
        return avail_val_ids

    @api.model
    def validate_configuration(
            self, value_ids=None, custom_vals=None,
            product_tmpl_id=False, final=True):
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
        if not value_ids:
            value_ids = self.value_ids.ids

        if product_tmpl_id:
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
        else:
            product_tmpl = self.product_tmpl_id

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        for line in product_tmpl.attribute_line_ids:
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
        custom_attr_ids = product_tmpl.attribute_line_ids.filtered(
            'custom').mapped('attribute_id').ids

        if not set(custom_vals.keys()) <= set(custom_attr_ids):
            return False

        # Check if there are multiple values passed for non-multi attributes
        mono_attr_lines = product_tmpl.attribute_line_ids.filtered(
            lambda l: not l.multi)

        for line in mono_attr_lines:
            if len(set(line.value_ids.ids) & set(value_ids)) > 1:
                return False
        return True

    @api.model
    def search_variant(
            self, value_ids=None, custom_vals=None, product_tmpl_id=None):
        """ Searches product.variants with given value_ids and custom values
            given in the custom_vals dict

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: product.product recordset of products matching domain
        """
        if not value_ids:
            value_ids = self.value_ids.ids

        if not custom_vals:
            custom_vals = self._get_custom_vals_dict()

        if not product_tmpl_id:
            session_template = self.product_tmpl_id
            if not session_template:
                raise ValidationError(_(
                    'Cannot conduct search on an empty config session without '
                    'product_tmpl_id kwarg')
                )
            product_tmpl_id = self.product_tmpl_id.id

        domain = self.get_variant_search_domain(
            product_tmpl_id=product_tmpl_id,
            value_ids=value_ids,
            custom_vals=custom_vals
        )

        products = self.env['product.product'].search(domain)

        # At this point, we might have found products with all of the passed
        # in values, but it might have more attributes!  These are NOT
        # matches
        more_attrs = products.filtered(
            lambda p:
            len(p.attribute_value_ids) != len(value_ids) or
            len(p.value_custom_ids) != len(custom_vals)
        )
        products -= more_attrs
        return products

    @api.multi
    def search_session(self, product_tmpl_id, parent_id=None):
        domain = self.get_session_search_domain(
            product_tmpl_id=product_tmpl_id,
            parent_id=parent_id
        )
        session = self.search(domain)
        return session

    @api.model
    def create_get_session(self, product_tmpl_id, parent_id=None):
        session = self.search_session(product_tmpl_id=product_tmpl_id,
                                      parent_id=parent_id)
        if session:
            return session[0]
        vals = self.get_session_vals(
            product_tmpl_id=product_tmpl_id,
            parent_id=parent_id
        )
        return self.create(vals)

    # TODO: Disallow duplicates

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
    def encode_custom_values(self, custom_vals):
        """ Hook to alter the values of the custom values before creating or writing

            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: list of custom values compatible with write and create
        """
        attr_obj = self.env['product.attribute']
        binary_attribute_ids = attr_obj.search([
            ('custom_type', '=', 'binary')]).ids

        custom_lines = []

        for key, val in custom_vals.items():
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


class ProductConfigSessionCustomValue(models.Model):
    _name = 'product.config.session.custom.value'
    _rec_name = 'attribute_id'

    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True
    )
    cfg_session_id = fields.Many2one(
        comodel_name='product.config.session',
        required=True,
        ondelete='cascade',
        string='Session'
    )
    value = fields.Char(
        string='Value',
        help='Custom value held as string',
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='product_config_session_custom_value_attachment_rel',
        column1='cfg_sesion_custom_val_id',
        column2='attachment_id',
        string='Attachments'
    )

    def eval(self):
        """Return custom value evaluated using the related custom field type"""
        field_type = self.attribute_id.custom_type
        if field_type == 'binary':
            vals = self.attachment_ids.mapped('datas')
            if len(vals) == 1:
                return vals[0]
            return vals
        elif field_type == 'int':
            return int(self.value)
        elif field_type == 'float':
            return float(self.value)
        return self.value

    @api.constrains('cfg_session_id', 'attribute_id')
    def unique_attribute(self):
        if len(self.cfg_session_id.custom_value_ids.filtered(
                lambda x: x.attribute_id == self.attribute_id)) > 1:
            raise ValidationError(
                _("Configuration cannot have the same value inserted twice")
            )

    # @api.constrains('cfg_session_id.value_ids')
    # def custom_only(self):
    #     """Verify that the attribute_id is not present in vals as well"""
    #     import ipdb;ipdb.set_trace()
    #     if self.cfg_session_id.value_ids.filtered(
    #             lambda x: x.attribute_id == self.attribute_id):
    #         raise ValidationError(
    #             _("Configuration cannot have a selected option and a custom "
    #               "value with the same attribute")
    #         )

    @api.constrains('attachment_ids', 'value')
    def check_custom_type(self):
        custom_type = self.attribute_id.custom_type
        if self.value and custom_type == 'binary':
            raise ValidationError(
                _("Attribute custom type is binary, attachments are the only "
                  "accepted values with this custom field type")
            )
        if self.attachment_ids and custom_type != 'binary':
            raise ValidationError(
                _("Attribute custom type must be 'binary' for saving "
                  "attachments to custom value")
            )
