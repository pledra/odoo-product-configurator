# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval

# TODO: Implement a default attribute value field/method to load up on wizard


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    @api.multi
    def copy(self, default=None):
        for attr in self:
            default.update({'name': attr.name + " (copy)"})
            attr = super(ProductAttribute, attr).copy(default)
            return attr

    @api.model
    def _get_nosearch_fields(self):
        """Return a list of custom field types that do not support searching"""
        return ['binary']

    @api.onchange('custom_type')
    def onchange_custom_type(self):
        if self.custom_type in self._get_nosearch_fields():
            self.search_ok = False

    CUSTOM_TYPES = [
        ('char', 'Char'),
        ('int', 'Integer'),
        ('float', 'Float'),
        ('text', 'Textarea'),
        ('color', 'Color'),
        ('binary', 'Attachment'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
    ]

    active = fields.Boolean(
        string='Active',
        default=True,
        help='By unchecking the active field you can '
        'disable a attribute without deleting it'
    )

    min_val = fields.Integer(string="Min Value", help="Minimum value allowed")
    max_val = fields.Integer(string="Max Value", help="Minimum value allowed")

    # TODO: Exclude self from result-set of dependency
    val_custom = fields.Boolean(
        string='Custom Value',
        help='Allow custom value for this attribute?'
    )
    custom_type = fields.Selection(
        selection=CUSTOM_TYPES,
        string='Field Type',
        size=64,
        help='The type of the custom field generated in the frontend'
    )

    description = fields.Text(string='Description', translate=True)

    search_ok = fields.Boolean(
        string='Searchable',
        help='When checking for variants with '
        'the same configuration, do we '
        'include this field in the search?'
    )

    required = fields.Boolean(
        string='Required',
        default=True,
        help='Determines the required value of this '
        'attribute though it can be change on '
        'the template level'
    )

    multi = fields.Boolean(
        string="Multi",
        help='Allow selection of multiple values for '
        'this attribute?'
    )

    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unit of Measure'
    )

    image = fields.Binary(string='Image')

    # TODO prevent the same attribute from being defined twice on the
    # attribute lines

    _order = 'sequence'

    @api.constrains('custom_type', 'search_ok')
    def check_searchable_field(self):
        nosearch_fields = self._get_nosearch_fields()
        if self.custom_type in nosearch_fields and self.search_ok:
            raise ValidationError(
                _("Selected custom field type '%s' is not searchable" %
                  self.custom_type)
            )

    def validate_custom_val(self, val):
        """ Pass in a desired custom value and ensure it is valid.
        Probaly should check type, etc, but let's assume fine for the moment.
        """
        self.ensure_one()
        if self.custom_type in ('int', 'float'):
            minv = self.min_val
            maxv = self.max_val
            val = literal_eval(val)
            if minv and maxv and (val < minv or val > maxv):
                raise ValidationError(
                    _("Selected custom value '%s' must be between %s and %s"
                        % (self.name, self.min_val, self.max_val))
                )
            elif minv and val < minv:
                raise ValidationError(
                    _("Selected custom value '%s' must be at least %s" %
                        (self.name, self.min_val))
                )
            elif maxv and val > maxv:
                raise ValidationError(
                    _("Selected custom value '%s' must be lower than %s" %
                        (self.name, self.max_val + 1))
                )


class ProductAttributeLine(models.Model):
    _inherit = 'product.attribute.line'

    @api.onchange('attribute_id')
    def onchange_attribute(self):
        self.value_ids = False
        self.required = self.attribute_id.required
        # TODO: Remove all dependencies pointed towards the attribute being
        # changed

    custom = fields.Boolean(
        string='Custom',
        help="Allow custom values for this attribute?"
    )
    required = fields.Boolean(
        string='Required',
        help="Is this attribute required?"
    )

    multi = fields.Boolean(
        string='Multi',
        help='Allow selection of multiple values for this attribute?'
    )

    sequence = fields.Integer(string='Sequence', default=10)

    # TODO: Order by dependencies first and then sequence so dependent fields
    # do not come before master field
    _order = 'product_tmpl_id, sequence, id'

    # TODO: Constraint not allowing introducing dependencies that do not exist
    # on the product.template


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.multi
    def copy(self, default=None):
        default.update({'name': self.name + " (copy)"})
        product = super(ProductAttributeValue, self).copy(default)
        return product

    active = fields.Boolean(
        string='Active',
        default=True,
        help='By unchecking the active field you can '
        'disable a attribute value without deleting it'
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Related Product'
    )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Use name_search as a domain restriction for the frontend to show
        only values set on the product template taking all the configuration
        restrictions into account.

        TODO: This only works when activating the selection not when typing
        """
        product_tmpl_id = self.env.context.get('_cfg_product_tmpl_id')
        if product_tmpl_id:
            # TODO: Avoiding browse here could be a good performance enhancer
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            tmpl_vals = product_tmpl.attribute_line_ids.mapped('value_ids')
            attr_restrict_ids = []
            preset_val_ids = []
            new_args = []
            for arg in args:
                # Restrict values only to value_ids set on product_template
                if arg[0] == 'id' and arg[1] == 'not in':
                    preset_val_ids = arg[2]
                    # TODO: Check if all values are available for configuration
                else:
                    new_args.append(arg)
            val_ids = set(tmpl_vals.ids)
            if preset_val_ids:
                val_ids -= set(arg[2])
            val_ids = product_tmpl.values_available(
                val_ids, preset_val_ids)
            new_args.append(('id', 'in', val_ids))
            mono_tmpl_lines = product_tmpl.attribute_line_ids.filtered(
                lambda l: not l.multi)
            for line in mono_tmpl_lines:
                line_val_ids = set(line.mapped('value_ids').ids)
                if line_val_ids & set(preset_val_ids):
                    attr_restrict_ids.append(line.attribute_id.id)
            if attr_restrict_ids:
                new_args.append(('attribute_id', 'not in', attr_restrict_ids))
            args = new_args
        res = super(ProductAttributeValue, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
        return res
    # TODO: Prevent unlinking custom options by overriding unlink

    # _sql_constraints = [
    #    ('unique_custom', 'unique(id,allow_custom_value)',
    #    'Only one custom value per dimension type is allowed')
    # ]


class ProductAttributeValueCustom(models.Model):

    @api.multi
    @api.depends('attribute_id', 'attribute_id.uom_id')
    def _compute_val_name(self):
        for attr_val_custom in self:
            uom = attr_val_custom.attribute_id.uom_id.name
            attr_val_custom.name = '%s%s' % (attr_val_custom.value, uom or '')

    _name = 'product.attribute.value.custom'

    name = fields.Char(
        string='Name',
        readonly=True,
        compute="_compute_val_name",
        store=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product ID',
        required=True,
        ondelete='cascade'
    )
    attribute_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='product_attr_val_custom_value_attachment_rel',
        column1='attr_val_custom_id',
        column2='attachment_id',
        string='Attachments'
    )
    value = fields.Char(
        string='Custom Value',
    )

    _sql_constraints = [
        ('attr_uniq', 'unique(product_id, attribute_id)',
         'Cannot have two custom values for the same attribute')
    ]
