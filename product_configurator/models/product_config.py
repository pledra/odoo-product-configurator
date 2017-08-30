# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
from ast import literal_eval


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
        for cfg_img in self:
            valid = cfg_img.product_tmpl_id.validate_configuration(
                cfg_img.value_ids.ids, final=False)
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
            lambda l: l != self).mapped('config_step_id')
        if self.config_step_id in cfg_steps:
            raise Warning(_('Cannot have a configuration step defined twice.'))


class ProductConfigSession(models.Model):
    _name = 'product.config.session'

    @api.multi
    @api.depends('value_ids', 'custom_value_ids', 'custom_value_ids.value')
    def _compute_cfg_price(self):
        for session in self:
            custom_vals = session._get_custom_vals_dict()
            price = session.product_tmpl_id.get_cfg_price(
                session.value_ids.ids, custom_vals)
            session.price = price['total']

    @api.multi
    def _get_custom_vals_dict(self):
        """Retrieve session custom values as a dictionary of the form
           {attribute_id: parsed_custom_value}"""
        self.ensure_one()
        custom_vals = {}
        for val in self.custom_value_ids:
            if val.attribute_id.custom_type in ['float', 'int']:
                custom_vals[val.attribute_id.id] = literal_eval(val.value)
            else:
                custom_vals[val.attribute_id.id] = val.value
        return custom_vals

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
        # TODO: Implement method to generate dict from custom vals
        custom_val_dict = {
            x.attribute_id.id: x.value or x.attachment_ids
            for x in self.custom_value_ids
        }
        valid = self.product_tmpl_id.validate_configuration(
            self.value_ids.ids, custom_val_dict)
        if valid:
            self.state = 'done'
        return valid

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
        for attr_id, vals in attr_val_dict.iteritems():
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
                ('id', 'in', custom_val_dict.keys()),
                ('custom_type', '=', 'binary')
            ]).ids
        for attr_id, vals in custom_val_dict.iteritems():
            if not vals:
                continue

            if 'custom_value_ids' not in update_vals:
                update_vals['custom_value_ids'] = []

            custom_vals = {'attribute_id': attr_id}

            if attr_id in binary_field_ids:
                attachments = [(0, 0, {
                    'name': val.get('name'),
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
        custom_val_dict = {
            x.attribute_id.id: x.value or x.attachment_ids
            for x in self.custom_value_ids
        }
        valid = self.product_tmpl_id.validate_configuration(
            self.value_ids.ids, custom_val_dict, final=False)
        if not valid:
            raise ValidationError(_('Invalid Configuration'))
        return res

    # TODO: Disallow duplicates


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
