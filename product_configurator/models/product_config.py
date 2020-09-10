from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.misc import formatLang


class ProductConfigDomain(models.Model):
    _name = "product.config.domain"
    _description = "Domain for Config Restrictions"

    @api.depends("implied_ids")
    def _get_trans_implied(self):
        """Computes the transitive closure of relation implied_ids"""

        def linearize(domains):
            trans_domains = domains
            for domain in domains:
                implied_domains = domain.implied_ids - domain
                if implied_domains:
                    trans_domains |= linearize(implied_domains)
            return trans_domains

        for domain in self:
            domain.trans_implied_ids = linearize(domain)

    def compute_domain(self):
        """ Returns a list of domains defined on a
        product.config.domain_line_ids and all implied_ids"""
        # TODO: Enable the usage of OR operators between implied_ids
        # TODO: Add implied_ids sequence field to enforce order of operations
        # TODO: Prevent circular dependencies
        computed_domain = []
        for domain in self:
            lines = domain.trans_implied_ids.mapped("domain_line_ids").sorted()
            if not lines:
                continue
            for line in lines[:-1]:
                if line.operator == "or":
                    computed_domain.append("|")
                computed_domain.append(
                    (line.attribute_id.id, line.condition, line.value_ids.ids)
                )
            # ensure 2 operands follow the last operator
            computed_domain.append(
                (
                    lines[-1].attribute_id.id,
                    lines[-1].condition,
                    lines[-1].value_ids.ids,
                )
            )
        return computed_domain

    name = fields.Char(string="Name", required=True, size=256)
    domain_line_ids = fields.One2many(
        comodel_name="product.config.domain.line",
        inverse_name="domain_id",
        string="Restrictions",
        required=True,
        copy=True,
    )
    implied_ids = fields.Many2many(
        comodel_name="product.config.domain",
        relation="product_config_domain_implied_rel",
        string="Inherited",
        column1="domain_id",
        column2="parent_id",
    )
    trans_implied_ids = fields.Many2many(
        comodel_name="product.config.domain",
        compute=_get_trans_implied,
        column1="domain_id",
        column2="parent_id",
        string="Transitively inherits",
    )


class ProductConfigDomainLine(models.Model):
    _name = "product.config.domain.line"
    _order = "sequence"
    _description = "Domain Line for Config Restrictions"

    def _get_domain_conditions(self):
        operators = [("in", "In"), ("not in", "Not In")]

        return operators

    def _get_domain_operators(self):
        andor = [("and", "And"), ("or", "Or")]

        return andor

    def _compute_template_attribute_value_ids(self):
        for domain in self:
            domain.template_attribute_value_ids = (
                domain._get_allowed_attribute_value_ids()
            )

    def _get_allowed_attribute_value_ids(self):
        self.ensure_one()
        product_template = self.env["product.template"]
        if self.env.context.get("product_tmpl_id"):
            product_template = product_template.browse(
                self.env.context.get("product_tmpl_id")
            )
        template_lines = product_template.attribute_line_ids
        attribute_values = self.attribute_id.value_ids
        return (
            product_template
            and (template_lines.mapped("value_ids") & attribute_values)
            or attribute_values
        )

    @api.onchange("attribute_id")
    def onchange_attribute_id(self):
        allowed_value_ids = self._get_allowed_attribute_value_ids()
        return {
            "domain": {"value_ids": [("id", "in", allowed_value_ids.ids)]},
            "value": {"value_ids": False},
        }

    template_attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        string="Template Attribute Values",
        compute="_compute_template_attribute_value_ids",
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute", string="Attribute", required=True
    )
    domain_id = fields.Many2one(
        comodel_name="product.config.domain", required=True, string="Rule"
    )
    condition = fields.Selection(
        selection=_get_domain_conditions, string="Condition", required=True
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="product_config_domain_line_attr_rel",
        column1="line_id",
        column2="attribute_id",
        string="Values",
        required=True,
    )
    operator = fields.Selection(
        selection=_get_domain_operators,
        string="Operators",
        default="and",
        required=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=1,
        help="Set the order of operations for evaluation domain lines",
    )


class ProductConfigLine(models.Model):
    _name = "product.config.line"
    _description = "Product Config Restrictions"
    _order = "product_tmpl_id, sequence, id"

    # TODO: Prevent config lines having dependencies that are not set in other
    # config lines
    # TODO: Prevent circular depdencies: Length -> Color, Color -> Length

    @api.onchange("attribute_line_id")
    def onchange_attribute(self):
        self.value_ids = False
        self.domain_id = False

    @api.depends(
        "product_tmpl_id",
        "attribute_line_id",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.config_line_ids",
    )
    def _compute_template_attribute_ids(self):
        for config_line in self:
            product_template = config_line.product_tmpl_id
            attribute_line_ids = product_template.attribute_line_ids
            config_line.template_attribute_ids = attribute_line_ids.mapped(
                "attribute_id"
            )

    template_attribute_ids = fields.Many2many(
        comodel_name="product.attribute",
        string="Template Attributes",
        compute="_compute_template_attribute_ids",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        ondelete="cascade",
        required=True,
    )
    attribute_line_id = fields.Many2one(
        comodel_name="product.template.attribute.line",
        string="Attribute Line",
        ondelete="cascade",
        required=True,
    )
    # TODO: Find a more elegant way to restrict the value_ids
    attr_line_val_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        related="attribute_line_id.value_ids",
        string="Attribute Line Values",
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        id1="cfg_line_id",
        id2="attr_val_id",
        string="Values",
    )
    domain_id = fields.Many2one(
        comodel_name="product.config.domain",
        required=True,
        string="Restrictions",
    )
    sequence = fields.Integer(string="Sequence", default=10)

    @api.constrains("value_ids")
    def check_value_attributes(self):
        """Values selected in config lines must belong to the
        attribute exist on linked attribute line"""
        for line in self:
            value_attributes = line.value_ids.mapped("attribute_id")
            if value_attributes != line.attribute_line_id.attribute_id:
                raise ValidationError(
                    _(
                        "Values must belong to the attribute of the "
                        "corresponding attribute_line set on the "
                        "configuration line"
                    )
                )


class ProductConfigImage(models.Model):
    _name = "product.config.image"
    _inherit = ["image.mixin"]
    _description = "Product Config Image"
    _order = "sequence"

    name = fields.Char("Name", size=128, required=True, translate=True)
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product",
        ondelete="cascade",
        required=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value", string="Configuration"
    )

    @api.constrains("value_ids")
    def _check_value_ids(self):
        """Check combination of values is possible according to given
        restrictions on linked product template"""
        cfg_session_obj = self.env["product.config.session"]
        for cfg_img in self:
            try:
                cfg_session_obj.validate_configuration(
                    value_ids=cfg_img.value_ids.ids,
                    product_tmpl_id=cfg_img.product_tmpl_id.id,
                    final=False,
                )
            except ValidationError:
                raise ValidationError(
                    _(
                        "Values entered for line '%s' generate "
                        "a incompatible configuration" % cfg_img.name
                    )
                )


class ProductConfigStep(models.Model):
    _name = "product.config.step"
    _description = "Product Config Steps"

    # TODO: Prevent values which have dependencies to be set in a
    #       step with higher sequence than the dependency

    name = fields.Char(string="Name", size=128, required=True, translate=True)


class ProductConfigStepLine(models.Model):
    _name = "product.config.step.line"
    _description = "Product Config Step Lines"
    _order = "sequence, config_step_id, id"

    name = fields.Char(related="config_step_id.name")
    config_step_id = fields.Many2one(
        comodel_name="product.config.step",
        string="Configuration Step",
        required=True,
    )
    attribute_line_ids = fields.Many2many(
        comodel_name="product.template.attribute.line",
        relation="config_step_line_attr_id_rel",
        column1="cfg_line_id",
        column2="attr_id",
        string="Attribute Lines",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        string="Product Template",
        ondelete="cascade",
        required=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)

    @api.constrains("config_step_id")
    def _check_config_step(self):
        """Prevent to add same step more than once on same product template"""
        for config_step in self:
            cfg_step_lines = config_step.product_tmpl_id.config_step_line_ids
            cfg_steps = cfg_step_lines.filtered(
                lambda line: line != config_step
            ).mapped("config_step_id")
            if config_step.config_step_id in cfg_steps:
                raise ValidationError(
                    _("Cannot have a configuration step defined twice.")
                )


class ProductConfigSession(models.Model):
    _name = "product.config.session"
    _description = "Product Config Session"

    @api.depends(
        "value_ids",
        "product_tmpl_id.list_price",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.attribute_line_ids.value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids",
        "product_tmpl_id.attribute_line_ids."
        "product_template_value_ids.price_extra",
    )
    def _compute_cfg_price(self):
        for session in self:
            if session.product_tmpl_id:
                price = session.get_cfg_price()
            else:
                price = 0.00
            session.price = price

    def get_custom_value_id(self):
        """Return record set of attribute value 'custom'"""
        custom_ext_id = "product_configurator.custom_attribute_value"
        custom_val_id = self.env.ref(custom_ext_id)
        return custom_val_id

    @api.model
    def _get_custom_vals_dict(self):
        """Retrieve session custom values as a dictionary of the form
           {attribute_id: parsed_custom_value}"""
        custom_vals = {}
        for val in self.custom_value_ids:
            if val.attribute_id.custom_type in ["float", "integer"]:
                custom_vals[val.attribute_id.id] = literal_eval(val.value)
            elif val.attribute_id.custom_type == "binary":
                custom_vals[val.attribute_id.id] = val.attachment_ids
            else:
                custom_vals[val.attribute_id.id] = val.value
        return custom_vals

    def _compute_config_step_name(self):
        """Get the config.step.line name using the string stored in config_step
         field of the session"""
        cfg_step_line_obj = self.env["product.config.step.line"]
        cfg_session_step_lines = self.mapped("config_step")
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

    @api.model
    def get_cfg_weight(self, value_ids=None, custom_vals=None):
        """ Computes the weight of the configured product based on the
        configuration passed in via value_ids and custom_values

        :param value_ids: list of attribute value_ids
        :param custom_vals: dictionary of custom attribute values
        :returns: final configuration weight"""

        if value_ids is None:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = {}

        product_tmpl = self.product_tmpl_id

        self = self.with_context({"active_id": product_tmpl.id})

        value_ids = self.flatten_val_ids(value_ids)

        weight_extra = 0.0
        product_attr_val_obj = self.env["product.template.attribute.value"]
        product_tmpl_attr_values = product_attr_val_obj.search(
            [
                ("product_tmpl_id", "in", product_tmpl.ids),
                ("product_attribute_value_id", "in", value_ids),
            ]
        )
        for product_tmpl_attr_val in product_tmpl_attr_values:
            weight_extra += product_tmpl_attr_val.weight_extra

        return product_tmpl.weight + weight_extra

    @api.depends(
        "value_ids",
        "product_tmpl_id",
        "product_tmpl_id.attribute_line_ids",
        "product_tmpl_id.attribute_line_ids.value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids",
        "product_tmpl_id.attribute_line_ids.product_template_value_ids"
        ".weight_extra",
    )
    def _compute_cfg_weight(self):
        for cfg_session in self:
            cfg_session.weight = cfg_session.get_cfg_weight()

    def _compute_currency_id(self):
        main_company = self.env["res.company"]._get_main_company()
        for session in self:
            template = session.product_tmpl_id
            session.currency_id = (
                template.company_id.sudo().currency_id.id
                or main_company.currency_id.id
            )

    name = fields.Char(string="Configuration Session Number", readonly=True)
    config_step = fields.Char(string="Configuration Step ID")
    config_step_name = fields.Char(
        compute="_compute_config_step_name", string="Configuration Step"
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        name="Configured Variant",
        ondelete="cascade",
    )
    product_tmpl_id = fields.Many2one(
        comodel_name="product.template",
        domain=[("config_ok", "=", True)],
        string="Configurable Template",
        required=True,
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="product_config_session_attr_values_rel",
        column1="cfg_session_id",
        column2="attr_val_id",
    )
    user_id = fields.Many2one(
        comodel_name="res.users", required=True, string="User"
    )
    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        string="Custom Values",
    )
    price = fields.Float(
        compute="_compute_cfg_price",
        string="Price",
        store=True,
        digits="Product Price",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
    )
    state = fields.Selection(
        string="State",
        required=True,
        selection=[("draft", "Draft"), ("done", "Done")],
        default="draft",
    )
    weight = fields.Float(
        string="Weight", compute="_compute_cfg_weight", digits="Stock Weight"
    )
    # Product preset
    product_preset_id = fields.Many2one(
        comodel_name="product.product",
        string="Preset",
        domain="[('product_tmpl_id', '=', product_tmpl_id),\
            ('config_preset_ok', '=', True)]",
    )

    def action_confirm(self, product_id=None):
        for session in self:
            if product_id is None:
                product_id = session.create_get_variant()
            session.write({"state": "done", "product_id": product_id.id})
        return True

    @api.constrains("state")
    def _check_product_id(self):
        for session in self.filtered(lambda s: s.state == "done"):
            if not session.product_id:
                raise ValidationError(
                    _(
                        "Finished configuration session must have a "
                        "product_id linked"
                    )
                )

    def update_session_configuration_value(self, vals, product_tmpl_id=None):
        """Update value of configuration in current session

        :param: vals: Dictionary of fields(of configution wizard) and values
        :param: product_tmpl_id: record set of preoduct template
        :return: True/False
        """
        self.ensure_one()
        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id

        product_configurator_obj = self.env["product.configurator"]
        field_prefix = product_configurator_obj._prefixes.get("field_prefix")
        custom_field_prefix = product_configurator_obj._prefixes.get(
            "custom_field_prefix"
        )

        custom_val = self.get_custom_value_id()

        attr_val_dict = {}
        custom_val_dict = {}
        for attr_line in product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            field_name = field_prefix + str(attr_id)
            custom_field_name = custom_field_prefix + str(attr_id)

            if field_name not in vals and custom_field_name not in vals:
                continue

            # Add attribute values from the client except custom attribute
            # If a custom value is being written, but field name is not in
            #   the write dictionary, then it must be a custom value!
            if vals.get(field_name, custom_val.id) != custom_val.id:
                if attr_line.multi and isinstance(vals[field_name], list):
                    if not vals[field_name]:
                        field_val = None
                    else:
                        field_val = vals[field_name][0][2]
                elif not attr_line.multi and isinstance(vals[field_name], int):
                    field_val = vals[field_name]
                else:
                    raise UserError(
                        _(
                            "An error occursed while parsing value for "
                            "attribute %s" % attr_line.attribute_id.name
                        )
                    )
                attr_val_dict.update({attr_id: field_val})
                # Ensure there is no custom value stored if we have switched
                # from custom value to selected attribute value.
                if attr_line.custom:
                    custom_val_dict.update({attr_id: False})
            elif attr_line.custom:
                val = vals.get(custom_field_name, False)
                if attr_line.attribute_id.custom_type == "binary":
                    # TODO: Add widget that enables multiple file uploads
                    val = [
                        {"name": "custom", "datas": vals[custom_field_name]}
                    ]
                custom_val_dict.update({attr_id: val})
                # Ensure there is no standard value stored if we have switched
                # from selected value to custom value.
                attr_val_dict.update({attr_id: False})

        self.update_config(attr_val_dict, custom_val_dict)

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
                lambda x: x.attribute_id.id == int(attr_id)
            ).ids
            # Remove all values for this attribute and add vals from dict
            value_ids = list(set(value_ids) - set(attr_val_ids))
            if not vals:
                continue
            if isinstance(vals, list):
                value_ids += vals
            elif isinstance(vals, int):
                value_ids.append(vals)

        if value_ids != self.value_ids.ids:
            update_vals.update({"value_ids": [(6, 0, value_ids)]})

        # Remove all custom values included in the custom_vals dict
        self.custom_value_ids.filtered(
            lambda x: x.attribute_id.id in custom_val_dict.keys()
        ).unlink()

        if custom_val_dict:
            binary_field_ids = (
                self.env["product.attribute"]
                .search(
                    [
                        ("id", "in", list(custom_val_dict.keys())),
                        ("custom_type", "=", "binary"),
                    ]
                )
                .ids
            )
        for attr_id, vals in custom_val_dict.items():
            if not vals:
                continue

            if "custom_value_ids" not in update_vals:
                update_vals["custom_value_ids"] = []

            custom_vals = {"attribute_id": attr_id}

            if attr_id in binary_field_ids:
                attachments = [
                    (
                        0,
                        0,
                        {"name": val.get("name"), "datas": val.get("datas")},
                    )
                    for val in vals
                ]
                custom_vals.update({"attachment_ids": attachments})
            else:
                custom_vals.update({"value": vals})

            update_vals["custom_value_ids"].append((0, 0, custom_vals))
        self.write(update_vals)

    def write(self, vals):
        """Validate configuration when writing new values to session"""
        # TODO: Issue warning when writing to value_ids or custom_val_ids

        res = super(ProductConfigSession, self).write(vals)
        if not self.product_tmpl_id:
            return res
        value_ids = self.value_ids.ids
        avail_val_ids = self.values_available(value_ids)
        if set(value_ids) - set(avail_val_ids):
            self.value_ids = [(6, 0, avail_val_ids)]
        try:
            self.validate_configuration(final=False)
        except ValidationError as ex:
            raise ValidationError("%s" % ex.name)
        except Exception:
            raise ValidationError(_("Invalid Configuration"))
        return res

    @api.model
    def create(self, vals):
        vals["name"] = self.env["ir.sequence"].next_by_code(
            "product.config.session"
        ) or _("New")
        product_tmpl = (
            self.env["product.template"]
            .browse(vals.get("product_tmpl_id"))
            .exists()
        )
        if product_tmpl:
            default_val_ids = (
                product_tmpl.attribute_line_ids.filtered(
                    lambda l: l.default_val
                )
                .mapped("default_val")
                .ids
            )
            value_ids = vals.get("value_ids")
            if value_ids:
                default_val_ids += value_ids[0][2]
            try:
                self.validate_configuration(
                    value_ids=default_val_ids,
                    final=False,
                    product_tmpl_id=product_tmpl.id,
                )
                # TODO: Remove if cond when PR with
                # raise error on github is merged
            except ValidationError as ex:
                raise ValidationError("%s" % ex.name)
            except Exception:
                raise ValidationError(
                    _(
                        "Default values provided generate an invalid "
                        "configuration"
                    )
                )
            vals.update({"value_ids": [(6, 0, default_val_ids)]})
        return super(ProductConfigSession, self).create(vals)

    def create_get_variant(self, value_ids=None, custom_vals=None):
        """ Creates a new product variant with the attributes passed
        via value_ids and custom_values or retrieves an existing
        one based on search result

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: new/existing product.product recordset

        """
        if self.product_tmpl_id.config_ok:
            self.validate_configuration()
        if value_ids is None:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        try:
            self.validate_configuration()
        except ValidationError as ex:
            raise ValidationError("%s" % ex.name)
        except Exception:
            raise ValidationError(_("Invalid Configuration"))

        duplicates = self.search_variant(
            value_ids=value_ids, product_tmpl_id=self.product_tmpl_id
        )
        if duplicates:
            return duplicates[:1]

        vals = self.get_variant_vals(value_ids, custom_vals)
        product_obj = (
            self.env["product.product"]
            .sudo()
            .with_context(mail_create_nolog=True)
        )
        variant = product_obj.sudo().create(vals)

        variant.message_post(
            body=_("Product created via configuration wizard"),
            author_id=self.env.user.partner_id.id,
        )

        return variant

    def _get_option_values(self, pricelist, value_ids=None):
        """Return only attribute values that have products attached with a
        price set to them"""
        if value_ids is None:
            value_ids = self.value_ids.ids

        value_obj = self.env["product.attribute.value"].with_context(
            {"pricelist": pricelist.id}
        )
        values = (
            value_obj.sudo()
            .browse(value_ids)
            .filtered(lambda x: x.product_id.price)
        )
        return values

    def get_components_prices(self, prices, pricelist, value_ids=None):
        """Return prices of the components which make up the final
        configured variant"""
        if value_ids is None:
            value_ids = self.value_ids.ids
        vals = self._get_option_values(pricelist, value_ids)
        for val in vals:
            prices["vals"].append(
                (
                    val.attribute_id.name,
                    val.product_id.name,
                    val.product_id.price,
                )
            )
            product = val.product_id.with_context({"pricelist": pricelist.id})
            product_prices = product.taxes_id.sudo().compute_all(
                price_unit=product.price,
                currency=pricelist.currency_id,
                quantity=1,
                product=self,
                partner=self.env.user.partner_id,
            )

            total_included = product_prices["total_included"]
            taxes = total_included - product_prices["total_excluded"]
            prices["taxes"] += taxes
            prices["total"] += total_included
        return prices

    @api.model
    def get_cfg_price(self, value_ids=None, custom_vals=None):
        """ Computes the price of the configured product based on the
            configuration passed in via value_ids and custom_values

        :param value_ids: list of attribute value_ids
        :param custom_vals: dictionary of custom attribute values
        :returns: final configuration price"""

        if value_ids is None:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = {}

        product_tmpl = self.product_tmpl_id
        self = self.with_context({"active_id": product_tmpl.id})

        value_ids = self.flatten_val_ids(value_ids)

        price_extra = 0.0
        attr_val_obj = self.env["product.attribute.value"]
        av_ids = attr_val_obj.browse(value_ids)
        extra_prices = attr_val_obj.get_attribute_value_extra_prices(
            product_tmpl_id=product_tmpl.id, pt_attr_value_ids=av_ids
        )
        price_extra = sum(extra_prices.values())
        return product_tmpl.list_price + price_extra

    def _get_config_image(self, value_ids=None, custom_vals=None, size=None):
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
        if value_ids is None:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        img_obj = self.product_tmpl_id
        max_matches = 0
        value_ids = self.flatten_val_ids(value_ids)
        for line in self.product_tmpl_id.config_image_ids:
            matches = len(set(line.value_ids.ids) & set(value_ids))
            if matches > max_matches:
                img_obj = line
                max_matches = matches
        return img_obj

    def get_config_image(self, value_ids=None, custom_vals=None, size=None):
        """
        Retreive the image object that most closely resembles the configuration
        code sent via value_ids list
        For more information check _get_config_image
        """
        config_image_id = self._get_config_image(
            value_ids=value_ids, custom_vals=custom_vals
        )
        return config_image_id.image_1920

    @api.model
    def get_variant_vals(self, value_ids=None, custom_vals=None, **kwargs):
        """ Hook to alter the values of the product variant before creation

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: dictionary of values to pass to product.create() method
         """
        self.ensure_one()

        if value_ids is None:
            value_ids = self.value_ids.ids

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        image = self.get_config_image(value_ids)
        ptav_ids = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", self.product_tmpl_id.id),
                ("product_attribute_value_id", "in", value_ids),
            ]
        )
        vals = {
            "product_tmpl_id": self.product_tmpl_id.id,
            "product_template_attribute_value_ids": [(6, 0, ptav_ids.ids)],
            "taxes_id": [(6, 0, self.product_tmpl_id.taxes_id.ids)],
            "image_1920": image,
        }
        return vals

    def get_session_search_domain(
        self, product_tmpl_id, state="draft", parent_id=None
    ):
        """Return domain to search session linked to given
        product template and current login user"""
        domain = [
            ("product_tmpl_id", "=", product_tmpl_id),
            ("user_id", "=", self.env.uid),
            ("state", "=", state),
        ]
        if parent_id:
            domain.append(("parent_id", "=", parent_id))
        return domain

    def get_session_vals(self, product_tmpl_id, parent_id=None, user_id=None):
        """Return the values for creating session"""
        if not user_id:
            user_id = self.env.user.id
        vals = {"product_tmpl_id": product_tmpl_id, "user_id": user_id}
        if parent_id:
            vals.update(parent_id=parent_id)
        return vals

    def get_next_step(
        self,
        state,
        product_tmpl_id=False,
        value_ids=False,
        custom_value_ids=False,
    ):
        """Find and return next step if exit. This usually
        implies the next configuration step (if any) defined via the
        config_step_line_ids on the product.template.
        """

        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id
        if value_ids is False:
            value_ids = self.value_ids
        if custom_value_ids is False:
            custom_value_ids = self.custom_value_ids
        if not state:
            state = self.config_step

        cfg_step_lines = product_tmpl_id.config_step_line_ids
        if not cfg_step_lines:
            if (value_ids or custom_value_ids) and state != "select":
                return False
            elif not (value_ids or custom_value_ids) and state != "select":
                raise UserError(
                    _(
                        "You must select at least one "
                        "attribute in order to configure a product"
                    )
                )
            else:
                return "configure"

        adjacent_steps = self.get_adjacent_steps()
        next_step = adjacent_steps.get("next_step")
        open_step_lines = list(
            map(lambda x: "%s" % (x), self.get_open_step_lines().ids)
        )

        session_config_step = self.config_step
        if (
            session_config_step
            and state != session_config_step
            and session_config_step in open_step_lines
        ):
            next_step = self.config_step
        else:
            next_step = str(next_step.id) if next_step else None
        if next_step:
            pass
        elif not (value_ids or custom_value_ids):
            raise UserError(
                _(
                    "You must select at least one "
                    "attribute in order to configure a product"
                )
            )
        else:
            return False
        return next_step

    # TODO: Should be renamed to get_active_step_line

    @api.model
    def get_active_step(self):
        """Attempt to return product.config.step.line object that has the id
        of the config session step stored as string"""
        cfg_step_line_obj = self.env["product.config.step.line"]

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

        if value_ids is None:
            value_ids = self.value_ids.ids

        open_step_lines = self.env["product.config.step.line"]

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
    def get_all_step_lines(self, product_tmpl_id=None):
        """
        Returns a recordset of configuration step lines of product_tmpl_id

        :param product_tmpl_id: record-set of product.template
        :returns: recordset of all configuration steps
        """
        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id

        open_step_lines = product_tmpl_id.config_step_line_ids
        return open_step_lines.sorted()

    @api.model
    def get_adjacent_steps(self, value_ids=None, active_step_line_id=None):
        """Returns the previous and next steps given the configuration passed
        via value_ids and the active step line passed via cfg_step_line_id."""

        # If there is no open step return empty dictionary

        if value_ids is None:
            value_ids = self.value_ids.ids

        if not active_step_line_id:
            active_step_line_id = self.get_active_step().id

        config_step_lines = self.product_tmpl_id.config_step_line_ids

        if not config_step_lines:
            return {}

        active_cfg_step_line = config_step_lines.filtered(
            lambda l: l.id == active_step_line_id
        )

        open_step_lines = self.get_open_step_lines(value_ids)

        if not active_cfg_step_line:
            return {"next_step": open_step_lines[0]}

        nr_steps = len(open_step_lines)

        adjacent_steps = {}

        for i, cfg_step in enumerate(open_step_lines):
            if cfg_step == active_cfg_step_line:
                adjacent_steps.update(
                    {
                        "next_step": None
                        if i + 1 == nr_steps
                        else open_step_lines[i + 1],
                        "previous_step": None
                        if i == 0
                        else open_step_lines[i - 1],
                    }
                )
        return adjacent_steps

    def check_and_open_incomplete_step(
        self, value_ids=None, custom_value_ids=None
    ):
        """ Check and open incomplete step if any
        :param value_ids: recordset of product.attribute.value
        """
        if value_ids is None:
            value_ids = self.value_ids
        if custom_value_ids is None:
            custom_value_ids = self.custom_value_ids
        custom_attr_selected = custom_value_ids.mapped("attribute_id")
        open_step_lines = self.get_open_step_lines()
        step_to_open = False
        for step in open_step_lines:
            unset_attr_line = step.attribute_line_ids.filtered(
                lambda attr_line: attr_line.required
                and not any(
                    [value in value_ids for value in attr_line.value_ids]
                )
                and not (
                    attr_line.custom
                    and attr_line.attribute_id in custom_attr_selected
                )
            )
            check_val_ids = unset_attr_line.mapped("value_ids")
            avail_val_ids = self.values_available(
                check_val_ids.ids,
                value_ids.ids,
                product_tmpl_id=self.product_tmpl_id,
            )
            if unset_attr_line and avail_val_ids:
                step_to_open = step
                break
        if step_to_open:
            return "%s" % (step_to_open.id)
        return False

    @api.model
    def get_variant_search_domain(self, product_tmpl_id, value_ids=None):
        """Method called by search_variant used to search duplicates in the
        database"""

        if value_ids is None:
            value_ids = self.value_ids.ids

        domain = [
            ("product_tmpl_id", "=", product_tmpl_id.id),
            ("config_ok", "=", True),
        ]
        pta_value_ids = self.env["product.template.attribute.value"].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_attribute_value_id", "in", value_ids),
            ]
        )
        for value_id in pta_value_ids:
            domain.append(
                ("product_template_attribute_value_ids", "=", value_id.id)
            )
        return domain

    def validate_domains_against_sels(
        self, domains, value_ids=None, custom_vals=None
    ):

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        if value_ids is None:
            value_ids = self.value_ids.ids

        # process domains as shown in this wikipedia pseudocode:
        # https://en.wikipedia.org/wiki/Polish_notation#Order_of_operations
        stack = []
        for domain in reversed(domains):
            if type(domain) == tuple:
                # evaluate operand and push to stack
                if domain[1] == "in":
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
        self,
        check_val_ids=None,
        value_ids=None,
        custom_vals=None,
        product_tmpl_id=None,
    ):
        """Determines whether the attr_values from the product_template
        are available for selection given the configuration ids and the
        dependencies set on the product template

        :param check_val_ids: list of attribute value ids to check for
                              availability
        :param value_ids: list of attribute value ids
        :param custom_vals: custom values dict {attr_id: custom_val}

        :returns: list of available attribute values
        """
        if check_val_ids is None:
            check_val_ids = self.value_ids.ids
        elif check_val_ids:
            check_val_ids = check_val_ids.copy()
        if not self.product_tmpl_id:
            product_tmpl = self.env["product.template"].browse(product_tmpl_id)
        else:
            product_tmpl = self.product_tmpl_id

        product_tmpl.ensure_one()

        if value_ids is None:
            value_ids = self.value_ids.ids
        elif value_ids:
            value_ids = value_ids.copy()

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()

        avail_val_ids = []
        for attr_val_id in check_val_ids:
            config_lines = product_tmpl.config_line_ids.filtered(
                lambda l: attr_val_id in l.value_ids.ids
            )
            domains = config_lines.mapped("domain_id").compute_domain()
            avail = self.validate_domains_against_sels(
                domains, value_ids, custom_vals
            )
            if avail:
                avail_val_ids.append(attr_val_id)
            elif attr_val_id in value_ids:
                value_ids.remove(attr_val_id)

        return avail_val_ids

    @api.model
    def get_extra_attribute_line_ids(self, product_template_id):
        """Retrieve attribute lines defined on the product_template_id
        which are not assigned to configuration steps"""

        extra_attribute_line_ids = (
            product_template_id.attribute_line_ids
            - product_template_id.config_step_line_ids.mapped(
                "attribute_line_ids"
            )
        )
        return extra_attribute_line_ids

    @api.model
    def validate_configuration(
        self,
        value_ids=None,
        custom_vals=None,
        product_tmpl_id=False,
        final=True,
    ):
        """ Verifies if the configuration values passed via value_ids and
        custom_vals are valid

        :param value_ids: list of attribute value ids
        :param custom_vals: custom values dict {attr_id: custom_val}
        :param final: boolean marker to check required attributes.
                      pass false to check non-final configurations

        :returns: Error dict with reason of validation failure
                  or True
        """
        # TODO: Raise ConfigurationError with reason
        # Check if required values are missing for final configuration
        if value_ids is None:
            value_ids = self.value_ids.ids

        if product_tmpl_id:
            product_tmpl = self.env["product.template"].browse(product_tmpl_id)
        else:
            product_tmpl = self.product_tmpl_id

        product_tmpl.ensure_one()

        if custom_vals is None:
            custom_vals = self._get_custom_vals_dict()
        open_step_lines = self.get_open_step_lines()
        attribute_line_ids = open_step_lines.mapped("attribute_line_ids")
        attribute_line_ids += self.get_extra_attribute_line_ids(
            product_template_id=product_tmpl
        )
        for line in attribute_line_ids:
            # Validate custom values
            attr = line.attribute_id
            if attr.id in custom_vals:
                attr.validate_custom_val(custom_vals[attr.id])
            if final:
                common_vals = set(value_ids) & set(line.value_ids.ids)
                custom_val = custom_vals.get(attr.id)
                avail_val_ids = self.values_available(
                    line.value_ids.ids,
                    value_ids,
                    product_tmpl_id=self.product_tmpl_id,
                )
                if (
                    line.required
                    and avail_val_ids
                    and not common_vals
                    and not custom_val
                ):
                    # TODO: Verify custom value type to be correct
                    raise ValidationError(
                        _("Required attribute '%s' is empty" % (attr.name))
                    )

        # Check if all all the values passed are not restricted
        avail_val_ids = self.values_available(
            value_ids, value_ids, product_tmpl_id=product_tmpl_id
        )
        if set(value_ids) - set(avail_val_ids):
            restrict_val = list(set(value_ids) - set(avail_val_ids))
            product_att_values = self.env["product.attribute.value"].browse(
                restrict_val
            )
            group_by_attr = {}
            for val in product_att_values:
                if val.attribute_id in group_by_attr:
                    group_by_attr[val.attribute_id] += val
                else:
                    group_by_attr[val.attribute_id] = val

            message = _("The following values are not available:")
            for attr, val in group_by_attr.items():
                message += "\n%s: %s" % (
                    attr.name,
                    ", ".join(val.mapped("name")),
                )
            raise ValidationError(message)

        # Check if custom values are allowed
        custom_attr_ids = (
            product_tmpl.attribute_line_ids.filtered("custom")
            .mapped("attribute_id")
            .ids
        )
        if not set(custom_vals.keys()) <= set(custom_attr_ids):
            custom_attrs_with_error = list(
                set(custom_vals.keys()) - set(custom_attr_ids)
            )
            custom_attrs_with_error = self.env["product.attribute"].browse(
                custom_attrs_with_error
            )
            error_message = _(
                "The following custom values are not permitted "
                "according to the product template - %s.\n\nIt is possible "
                "that a change has been made to allowed custom values "
                "while your configuration was in process. Please reset your "
                "current session and start over or contact your administrator"
                " in order to proceed."
            )
            message_vals = ""
            for attr_id in custom_attrs_with_error:
                message_vals += "\n%s: %s" % (
                    attr_id.name,
                    custom_vals.get(attr_id.id),
                )
            raise ValidationError(error_message % (message_vals))

        # Check if there are multiple values passed for non-multi attributes
        mono_attr_lines = product_tmpl.attribute_line_ids.filtered(
            lambda l: not l.multi
        )
        attrs_with_error = {}
        for line in mono_attr_lines:
            if len(set(line.value_ids.ids) & set(value_ids)) > 1:
                wrong_vals = self.env["product.attribute.value"].browse(
                    set(line.value_ids.ids) & set(value_ids)
                )
                attrs_with_error[line.attribute_id] = wrong_vals
        if attrs_with_error:
            error_message = _(
                "The following multi values are not permitted "
                "according to the product template - %s.\n\nIt is possible "
                "that a change has been made to allowed multi values "
                "while your configuration was in process. Please reset your "
                "current session and start over or contact your administrator"
                " in order to proceed."
            )
            message_vals = ""
            for attr_id, vals in attrs_with_error.items():
                message_vals += "\n%s: %s" % (
                    attr_id.name,
                    ", ".join(vals.mapped("name")),
                )
            raise ValidationError(error_message % (message_vals))
        return True

    @api.model
    def search_variant(self, value_ids=None, product_tmpl_id=None):
        """ Searches product.variants with given value_ids and custom values
            given in the custom_vals dict

            :param value_ids: list of product.attribute.values ids
            :param custom_vals: dict {product.attribute.id: custom_value}

            :returns: product.product recordset of products matching domain
        """
        if value_ids is None:
            value_ids = self.value_ids.ids

        custom_value_id = self.get_custom_value_id()
        value_ids = list(set(value_ids) - set(custom_value_id.ids))

        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id
            if not product_tmpl_id:
                raise ValidationError(
                    _(
                        "Cannot conduct search on an empty config session "
                        "without product_tmpl_id kwarg"
                    )
                )

        domain = self.get_variant_search_domain(
            product_tmpl_id=product_tmpl_id, value_ids=value_ids
        )
        products = self.env["product.product"].search(domain)

        # At this point, we might have found products with all of the passed
        # in values, but it might have more attributes!  These are NOT
        # matches
        more_attrs = products.filtered(
            lambda p: len(p.product_template_attribute_value_ids)
            != len(value_ids)
        )
        products -= more_attrs
        return products

    def search_session(self, product_tmpl_id, parent_id=None):
        domain = self.get_session_search_domain(
            product_tmpl_id=product_tmpl_id, parent_id=parent_id
        )
        session = self.search(domain, order="create_date desc", limit=1)
        return session

    @api.model
    def create_get_session(
        self, product_tmpl_id, parent_id=None, force_create=False, user_id=None
    ):
        if not force_create:
            session = self.search_session(
                product_tmpl_id=product_tmpl_id, parent_id=parent_id
            )
            if session:
                return session
        vals = self.get_session_vals(
            product_tmpl_id=product_tmpl_id,
            parent_id=parent_id,
            user_id=user_id,
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

    def formatPrices(self, prices=None, dp="Product Price"):
        if prices is None:
            prices = {}
        dp = None
        prices["taxes"] = formatLang(
            self.env, prices["taxes"], monetary=True, dp=dp
        )
        prices["total"] = formatLang(
            self.env, prices["total"], monetary=True, dp=dp
        )
        prices["vals"] = [
            (v[0], v[1], formatLang(self.env, v[2], monetary=True, dp=dp))
            for v in prices["vals"]
        ]
        return prices

    def encode_custom_values(self, custom_vals):
        """ Hook to alter the values of the custom values before creating
            or writing
            :param custom_vals: dict {product.attribute.id: custom_value}
            :returns: list of custom values compatible with write and create
        """
        attr_obj = self.env["product.attribute"]
        binary_attribute_ids = attr_obj.search(
            [("custom_type", "=", "binary")]
        ).ids
        custom_lines = []

        for key, val in custom_vals.items():
            custom_vals = {"attribute_id": key}
            # TODO: Is this extra check neccesairy as we already make
            # the check in validate_configuration?
            attr_obj.browse(key).validate_custom_val(val)
            if key in binary_attribute_ids:
                custom_vals.update({"attachment_ids": [(6, 0, val.ids)]})
            else:
                custom_vals.update({"value": val})
            custom_lines.append((0, 0, custom_vals))
        return custom_lines

    @api.model
    def get_child_specification(self, model, parent):
        """return dictiory of onchange specification by
        appending parent before each key"""
        model_obj = self.env[model]
        specs = model_obj._onchange_spec()
        new_specs = {}
        for key, val in specs.items():
            new_specs["%s.%s" % (parent, key)] = val
        return new_specs

    @api.model
    def get_onchange_specifications(self, model):
        """return onchange specification
        - same functionality by _onchange_spec
        - needed this method because odoo don't add specification for fields
        one2many or many2many there is view-reference(using : tree_view_ref)
        intead of view in that field"""
        model_obj = self.env[model]
        specs = model_obj._onchange_spec()
        for name, field in model_obj._fields.items():
            if field.type not in ["one2many", "many2many"]:
                continue
            ch_specs = self.get_child_specification(
                model=field.comodel_name, parent=name
            )
            specs.update(ch_specs)
        return specs

    @api.model
    def get_vals_to_write(self, values, model):
        """Return values in formate excepted by write/create methods
        - same functionality by _convert_to_write
        - needed this method because odoo don't call convert to write
        for the many2many/one2many fields"""
        model_obj = self.env[model]
        values = model_obj._convert_to_write(values)
        fields = model_obj._fields
        for key, vals in values.items():
            if not isinstance(vals, list):
                continue
            new_lst = []
            for line in vals:
                new_line = line
                if line and isinstance(line[-1], dict):
                    new_line = line[:-1] + (
                        self.get_vals_to_write(
                            values=line[-1], model=fields[key].comodel_name
                        ),
                    )
                new_lst.append(new_line)
            values[key] = new_lst
        return values


class ProductConfigSessionCustomValue(models.Model):
    _name = "product.config.session.custom.value"
    _rec_name = "attribute_id"
    _description = "Product Config Session Custom Value"

    @api.depends("attribute_id", "attribute_id.uom_id")
    def _compute_val_name(self):
        for attr_val_custom in self:
            uom = attr_val_custom.attribute_id.uom_id.name
            attr_val_custom.name = "%s%s" % (
                attr_val_custom.value,
                (" %s" % uom) or "",
            )

    name = fields.Char(
        string="Name", readonly=True, compute="_compute_val_name", store=True
    )
    attribute_id = fields.Many2one(
        comodel_name="product.attribute", string="Attribute", required=True
    )
    cfg_session_id = fields.Many2one(
        comodel_name="product.config.session",
        required=True,
        ondelete="cascade",
        string="Session",
    )
    value = fields.Char(string="Value", help="Custom value held as string")
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        relation="product_config_session_custom_value_attachment_rel",
        column1="cfg_sesion_custom_val_id",
        column2="attachment_id",
        string="Attachments",
    )

    def eval(self):
        """Return custom value evaluated using the related custom field type"""
        field_type = self.attribute_id.custom_type
        if field_type == "binary":
            vals = self.attachment_ids.mapped("datas")
            if len(vals) == 1:
                return vals[0]
            return vals
        elif field_type == "integer":
            return int(self.value)
        elif field_type == "float":
            return float(self.value)
        return self.value

    @api.constrains("cfg_session_id", "attribute_id")
    def unique_attribute(self):
        for custom_val in self:
            if (
                len(
                    custom_val.cfg_session_id.custom_value_ids.filtered(
                        lambda x: x.attribute_id == custom_val.attribute_id
                    )
                )
                > 1
            ):
                raise ValidationError(
                    _(
                        "Configuration cannot have the "
                        "same value inserted twice"
                    )
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

    @api.constrains("attachment_ids", "value")
    def check_custom_type(self):
        for custom_val in self:
            custom_type = custom_val.attribute_id.custom_type
            if custom_val.value and custom_type == "binary":
                raise ValidationError(
                    _(
                        "Attribute custom type is binary, attachments are the "
                        "only accepted values with this custom field type"
                    )
                )
            if custom_val.attachment_ids and custom_type != "binary":
                raise ValidationError(
                    _(
                        "Attribute custom type must be 'binary' for saving "
                        "attachments to custom value"
                    )
                )
