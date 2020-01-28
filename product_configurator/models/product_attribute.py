from ast import literal_eval

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductAttribute(models.Model):
    _inherit = "product.attribute"
    _order = "sequence"

    def copy(self, default=None):
        """Add ' (Copy)' in name to prevent attribute
        having same name while copying"""
        if not default:
            default = {}
        new_attrs = self.env["product.attribute"]
        for attr in self:
            default.update({"name": attr.name + " (copy)"})
            new_attrs += super(ProductAttribute, attr).copy(default)
        return new_attrs

    @api.model
    def _get_nosearch_fields(self):
        """Return a list of custom field types that do not support searching"""
        return ["binary"]

    @api.onchange("custom_type")
    def onchange_custom_type(self):
        if self.custom_type in self._get_nosearch_fields():
            self.search_ok = False
        if self.custom_type not in ("integer", "float"):
            self.min_val = False
            self.max_val = False

    @api.onchange("val_custom")
    def onchange_val_custom_field(self):
        if not self.val_custom:
            self.custom_type = False

    CUSTOM_TYPES = [
        ("char", "Char"),
        ("integer", "Integer"),
        ("float", "Float"),
        ("text", "Textarea"),
        ("color", "Color"),
        ("binary", "Attachment"),
        ("date", "Date"),
        ("datetime", "DateTime"),
    ]

    active = fields.Boolean(
        string="Active",
        default=True,
        help="By unchecking the active field you can "
        "disable a attribute without deleting it",
    )
    min_val = fields.Integer(string="Min Value", help="Minimum value allowed")
    max_val = fields.Integer(string="Max Value", help="Maximum value allowed")

    # TODO: Exclude self from result-set of dependency
    val_custom = fields.Boolean(
        string="Custom Value", help="Allow custom value for this attribute?"
    )
    custom_type = fields.Selection(
        selection=CUSTOM_TYPES,
        string="Field Type",
        size=64,
        help="The type of the custom field generated in the frontend",
    )
    description = fields.Text(string="Description", translate=True)
    search_ok = fields.Boolean(
        string="Searchable",
        help="When checking for variants with "
        "the same configuration, do we "
        "include this field in the search?",
    )
    required = fields.Boolean(
        string="Required",
        default=True,
        help="Determines the required value of this "
        "attribute though it can be change on "
        "the template level",
    )
    multi = fields.Boolean(
        string="Multi",
        help="Allow selection of multiple values for " "this attribute?",
    )
    uom_id = fields.Many2one(comodel_name="uom.uom", string="Unit of Measure")
    image = fields.Binary(string="Image")

    # TODO prevent the same attribute from being defined twice on the
    # attribute lines

    @api.constrains("custom_type", "search_ok")
    def check_searchable_field(self):
        for attribute in self:
            nosearch_fields = attribute._get_nosearch_fields()
            if (
                attribute.custom_type in nosearch_fields
                and attribute.search_ok
            ):
                raise ValidationError(
                    _(
                        "Selected custom field type '%s' is not searchable"
                        % attribute.custom_type
                    )
                )

    def validate_custom_val(self, val):
        """ Pass in a desired custom value and ensure it is valid.
        Probaly should check type, etc, but let's assume fine for the moment.
        """
        self.ensure_one()
        if self.custom_type in ("integer", "float"):
            minv = self.min_val
            maxv = self.max_val
            val = literal_eval(str(val))
            if minv and maxv and (val < minv or val > maxv):
                raise ValidationError(
                    _(
                        "Selected custom value '%s' must be between %s and %s"
                        % (self.name, self.min_val, self.max_val)
                    )
                )
            elif minv and val < minv:
                raise ValidationError(
                    _(
                        "Selected custom value '%s' must be at least %s"
                        % (self.name, self.min_val)
                    )
                )
            elif maxv and val > maxv:
                raise ValidationError(
                    _(
                        "Selected custom value '%s' must be lower than %s"
                        % (self.name, self.max_val + 1)
                    )
                )

    @api.constrains("min_val", "max_val")
    def _check_constraint_min_max_value(self):
        """Prevent to add Maximun value less than minimum value"""
        for attribute in self:
            if attribute.custom_type not in ("integer", "float"):
                continue
            minv = attribute.min_val
            maxv = attribute.max_val
            if maxv and minv and maxv < minv:
                raise ValidationError(
                    _("Maximum value must be greater than Minimum value")
                )


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"
    _order = "product_tmpl_id, sequence, id"
    # TODO: Order by dependencies first and then sequence so dependent fields
    # do not come before master field

    @api.onchange("attribute_id")
    def onchange_attribute(self):
        """Set default value of required/multi/cutom from attribute"""
        self.value_ids = False
        self.required = self.attribute_id.required
        self.multi = self.attribute_id.multi
        self.custom = self.attribute_id.val_custom
        # TODO: Remove all dependencies pointed towards the attribute being
        # changed

    @api.onchange("value_ids")
    def onchange_values(self):
        if self.default_val and self.default_val not in self.value_ids:
            self.default_val = None

    custom = fields.Boolean(
        string="Custom", help="Allow custom values for this attribute?"
    )
    required = fields.Boolean(
        string="Required", help="Is this attribute required?"
    )
    multi = fields.Boolean(
        string="Multi",
        help="Allow selection of multiple values for this attribute?",
    )
    default_val = fields.Many2one(
        comodel_name="product.attribute.value", string="Default Value"
    )

    sequence = fields.Integer(string="Sequence", default=10)

    @api.constrains("value_ids", "default_val")
    def _check_default_values(self):
        """default value should not be outside of the
        values selected in attribute line"""
        for line in self.filtered(lambda l: l.default_val):
            if line.default_val not in line.value_ids:
                raise ValidationError(
                    _(
                        "Default values for each attribute line must exist in "
                        "the attribute values (%s: %s)"
                        % (line.attribute_id.name, line.default_val.name)
                    )
                )

    @api.constrains("active", "value_ids", "attribute_id")
    def _check_valid_values(self):
        """Overwrite to save attribute line without
        values when custom is true"""
        for ptal in self:
            # Customization
            if ptal.active and not ptal.value_ids and not ptal.custom:
                # Old code
                # if ptal.active and not ptal.value_ids:
                # Customization End
                raise ValidationError(
                    _(
                        "The attribute %s must have at least one value for "
                        "the product %s."
                    )
                    % (
                        ptal.attribute_id.display_name,
                        ptal.product_tmpl_id.display_name,
                    )
                )
            for pav in ptal.value_ids:
                if pav.attribute_id != ptal.attribute_id:
                    raise ValidationError(
                        _(
                            "On the product %s you cannot associate the "
                            "value %s with the attribute %s because they "
                            "do not match."
                        )
                        % (
                            ptal.product_tmpl_id.display_name,
                            pav.display_name,
                            ptal.attribute_id.display_name,
                        )
                    )
        return True


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    def copy(self, default=None):
        """Add ' (Copy)' in name to prevent attribute
        having same name while copying"""
        if not default:
            default = {}
        default.update({"name": self.name + " (copy)"})
        product = super(ProductAttributeValue, self).copy(default)
        return product

    active = fields.Boolean(
        string="Active",
        default=True,
        help="By unchecking the active field you can "
        "disable a attribute value without deleting it",
    )
    product_id = fields.Many2one(
        comodel_name="product.product", string="Related Product"
    )
    image = fields.Binary(
        string="Image",
        attachment=True,
        help="Attribute value image (Display on website for radio buttons)",
    )

    @api.model
    def get_attribute_value_extra_prices(
        self, product_tmpl_id, pt_attr_value_ids, pricelist=None
    ):
        extra_prices = {}
        if not pricelist:
            pricelist = self.env.user.partner_id.property_product_pricelist

        related_product_av_ids = self.env["product.attribute.value"].search(
            [("id", "in", pt_attr_value_ids.ids), ("product_id", "!=", False)]
        )
        extra_prices = {
            av.id: av.product_id.with_context(pricelist=pricelist.id).price
            for av in related_product_av_ids
        }
        remaining_av_ids = pt_attr_value_ids - related_product_av_ids
        pe_lines = self.env["product.template.attribute.value"].search(
            [
                ("product_attribute_value_id", "in", remaining_av_ids.ids),
                ("product_tmpl_id", "=", product_tmpl_id),
            ]
        )
        for line in pe_lines:
            attr_val_id = line.product_attribute_value_id
            if attr_val_id.id not in extra_prices:
                extra_prices[attr_val_id.id] = 0
            extra_prices[attr_val_id.id] += line.price_extra
        return extra_prices

    def name_get(self):
        res = super(ProductAttributeValue, self).name_get()
        if not self._context.get("show_price_extra"):
            return res
        product_template_id = self.env.context.get("active_id", False)

        price_precision = self.env["decimal.precision"].precision_get(
            "Product Price"
        )
        extra_prices = self.get_attribute_value_extra_prices(
            product_tmpl_id=product_template_id, pt_attr_value_ids=self
        )

        res_prices = []
        for val in res:
            price_extra = extra_prices.get(val[0])
            if price_extra:
                val = (
                    val[0],
                    "%s ( +%s )"
                    % (
                        val[1],
                        ("{0:,.%sf}" % (price_precision)).format(price_extra),
                    ),
                )
            res_prices.append(val)
        return res_prices

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Use name_search as a domain restriction for the frontend to show
        only values set on the product template taking all the configuration
        restrictions into account.

        TODO: This only works when activating the selection not when typing
        """
        product_tmpl_id = self.env.context.get("_cfg_product_tmpl_id")
        if product_tmpl_id:
            # TODO: Avoiding browse here could be a good performance enhancer
            product_tmpl = self.env["product.template"].browse(product_tmpl_id)
            tmpl_vals = product_tmpl.attribute_line_ids.mapped("value_ids")
            attr_restrict_ids = []
            preset_val_ids = []
            new_args = []
            for arg in args:
                # Restrict values only to value_ids set on product_template
                if arg[0] == "id" and arg[1] == "not in":
                    preset_val_ids = arg[2]
                    # TODO: Check if all values are available for configuration
                else:
                    new_args.append(arg)
            val_ids = set(tmpl_vals.ids)
            if preset_val_ids:
                val_ids -= set(arg[2])
            val_ids = self.env["product.config.session"].values_available(
                val_ids, preset_val_ids, product_tmpl_id=product_tmpl_id
            )
            new_args.append(("id", "in", val_ids))
            mono_tmpl_lines = product_tmpl.attribute_line_ids.filtered(
                lambda l: not l.multi
            )
            for line in mono_tmpl_lines:
                line_val_ids = set(line.mapped("value_ids").ids)
                if line_val_ids & set(preset_val_ids):
                    attr_restrict_ids.append(line.attribute_id.id)
            if attr_restrict_ids:
                new_args.append(("attribute_id", "not in", attr_restrict_ids))
            args = new_args
        res = super(ProductAttributeValue, self).name_search(
            name=name, args=args, operator=operator, limit=limit
        )
        return res

    # TODO: Prevent unlinking custom options by overriding unlink

    # _sql_constraints = [
    #    ('unique_custom', 'unique(id,allow_custom_value)',
    #    'Only one custom value per dimension type is allowed')
    # ]


class ProductAttributePrice(models.Model):
    _inherit = "product.template.attribute.value"
    # Leverage product.template.attribute.value to compute the extra weight
    # each attribute adds

    weight_extra = fields.Float(
        string="Attribute Weight Extra", digits="Stock Weight"
    )


class ProductAttributeValueLine(models.Model):
    _name = "product.attribute.value.line"
    _description = "Product Attribute Value Line"
    _order = "sequence"

    sequence = fields.Integer(string="Sequence", default=10)
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        ondelete="cascade",
        required=True,
    )
    value_id = fields.Many2one(
        comodel_name="product.attribute.value",
        required="True",
        string="Attribute Value",
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute", related="value_id.attribute_id"
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="product_attribute_value_product_attribute_value_line_rel",
        column1="product_attribute_value_line_id",
        column2="product_attribute_value_id",
        string="Values Configuration",
    )
    product_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="product_attr_values_attr_values_rel",
        column1="product_val_id",
        column2="attr_val_id",
        compute="_compute_get_value_id",
        store=True,
    )

    @api.depends(
        "product_tmpl_id",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.attribute_line_ids.value_ids",
    )
    def _compute_get_value_id(self):
        for attr_val_line in self:
            template = attr_val_line.product_tmpl_id
            value_list = template.attribute_line_ids.mapped("value_ids")
            attr_val_line.product_value_ids = [(6, 0, value_list.ids)]

    @api.constrains("value_ids")
    def _validate_configuration(self):
        """Ensure that the passed configuration in value_ids is a valid"""
        cfg_session_obj = self.env["product.config.session"]
        for attr_val_line in self:
            value_ids = attr_val_line.value_ids.ids
            value_ids.append(attr_val_line.value_id.id)
            valid = cfg_session_obj.validate_configuration(
                value_ids=value_ids,
                product_tmpl_id=attr_val_line.product_tmpl_id.id,
                final=False,
            )
            if not valid:
                raise ValidationError(
                    _(
                        "Values provided to the attribute value line are "
                        "incompatible with the current rules"
                    )
                )
