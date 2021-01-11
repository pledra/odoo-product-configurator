from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from mako.template import Template
from mako.runtime import Context
from odoo.tools.safe_eval import safe_eval
from io import StringIO
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends("product_variant_ids.product_tmpl_id")
    def _compute_product_variant_count(self):
        """For configurable products return the number of variants configured or
        1 as many views and methods trigger only when a template has at least
        one variant attached. Since we create them from the template we should
        have access to them always"""
        super(ProductTemplate, self)._compute_product_variant_count()
        for product_tmpl in self:
            config_ok = product_tmpl.config_ok
            variant_count = product_tmpl.product_variant_count
            if config_ok and not variant_count:
                product_tmpl.product_variant_count = 1

    @api.depends("attribute_line_ids.value_ids")
    def _compute_template_attr_vals(self):
        """Compute all attribute values added in attribute line on
        product template"""
        for product_tmpl in self:
            if product_tmpl.config_ok:
                value_ids = product_tmpl.attribute_line_ids.mapped("value_ids")
                product_tmpl.attribute_line_val_ids = value_ids
            else:
                product_tmpl.attribute_line_val_ids = False

    @api.constrains("attribute_line_ids", "attribute_value_line_ids")
    def check_attr_value_ids(self):
        """Check attribute lines don't have some attribute value that
        is not present in attribute lines of that product template"""
        for product_tmpl in self:
            if not product_tmpl.env.context.get("check_constraint", True):
                continue
            attr_val_lines = product_tmpl.attribute_value_line_ids
            attr_val_ids = attr_val_lines.mapped("value_ids")
            if not attr_val_ids <= product_tmpl.attribute_line_val_ids:
                raise ValidationError(
                    _(
                        "All attribute values used in attribute value lines "
                        "must be defined in the attribute lines of the "
                        "template"
                    )
                )

    @api.constrains("attribute_value_line_ids")
    def _validate_unique_config(self):
        """Check for duplicate configurations for the same
        attribute value in image lines"""
        for template in self:
            attr_val_line_vals = template.attribute_value_line_ids.read(
                ["value_id", "value_ids"], load=False
            )
            attr_val_line_vals = [
                (line["value_id"], tuple(line["value_ids"]))
                for line in attr_val_line_vals
            ]
            if len(set(attr_val_line_vals)) != len(attr_val_line_vals):
                raise ValidationError(
                    _(
                        "You cannot have a duplicate configuration for the "
                        "same value"
                    )
                )

    config_ok = fields.Boolean(string="Can be Configured")

    config_line_ids = fields.One2many(
        comodel_name="product.config.line",
        inverse_name="product_tmpl_id",
        string="Attribute Dependencies",
        copy=False,
    )

    config_image_ids = fields.One2many(
        comodel_name="product.config.image",
        inverse_name="product_tmpl_id",
        string="Configuration Images",
        copy=True,
    )

    attribute_value_line_ids = fields.One2many(
        comodel_name="product.attribute.value.line",
        inverse_name="product_tmpl_id",
        string="Attribute Value Lines",
        copy=True,
    )

    attribute_line_val_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        compute="_compute_template_attr_vals",
        store=False,
    )

    config_step_line_ids = fields.One2many(
        comodel_name="product.config.step.line",
        inverse_name="product_tmpl_id",
        string="Configuration Lines",
        copy=False,
    )

    mako_tmpl_name = fields.Text(
        string="Variant name",
        help="Generate Name based on Mako Template",
        copy=True,
    )

    # We are calculating weight of variants based on weight of
    # product-template so that no need of compute and inverse on this
    weight = fields.Float(
        compute="_compute_weight",
        inverse="_set_weight",
        search="_search_weight",
        store=False,
    )
    weight_dummy = fields.Float(
        string="Manual Weight",
        digits="Stock Weight",
        help="Manual setting of product template weight",
    )

    def _compute_weight(self):
        config_products = self.filtered(lambda template: template.config_ok)
        for product in config_products:
            product.weight = product.weight_dummy
        standard_products = self - config_products
        super(ProductTemplate, standard_products)._compute_weight()

    def _set_weight(self):
        for product_tmpl in self:
            product_tmpl.weight_dummy = product_tmpl.weight
            if not product_tmpl.config_ok:
                super(ProductTemplate, product_tmpl)._set_weight()

    def _search_weight(self, operator, value):
        return [("weight_dummy", operator, value)]

    def get_product_attribute_values_action(self):
        self.ensure_one()
        action = self.env.ref("product.product_attribute_value_action").read()[
            0
        ]
        value_ids = self.attribute_line_ids.mapped(
            "product_template_value_ids"
        ).ids
        action["domain"] = [("id", "in", value_ids)]
        context = safe_eval(action["context"], {"active_id": self.id})
        context.update({"active_id": self.id})
        action["context"] = context
        return action

    def _check_default_values(self):
        default_val_ids = (
            self.attribute_line_ids.filtered(lambda l: l.default_val)
            .mapped("default_val")
            .ids
        )

        cfg_session_obj = self.env["product.config.session"]
        try:
            cfg_session_obj.validate_configuration(
                value_ids=default_val_ids, product_tmpl_id=self.id, final=False
            )
        except ValidationError as ex:
            raise ValidationError(ex.name)
        except Exception:
            raise ValidationError(
                _("Default values provided generate an invalid configuration")
            )

    @api.constrains("config_line_ids", "attribute_line_ids")
    def _check_default_value_domains(self):
        for template in self:
            try:
                template._check_default_values()
            except ValidationError as e:
                raise ValidationError(
                    _(
                        "Restrictions added make the current default values "
                        "generate an invalid configuration.\
                      \n%s"
                    )
                    % (e.name)
                )

    def toggle_config(self):
        for record in self:
            record.config_ok = not record.config_ok

    def _create_variant_ids(self):
        """ Prevent configurable products from creating variants as these serve
            only as a template for the product configurator"""
        templates = self.filtered(lambda t: not t.config_ok)
        if not templates:
            return None
        return super(ProductTemplate, templates)._create_variant_ids()

    def unlink(self):
        """- Prevent the removal of configurable product templates
            from variants
        - Patch for check access rights of user(configurable products)"""
        configurable_templates = self.filtered(
            lambda template: template.config_ok
        )
        if configurable_templates:
            configurable_templates[:1].check_config_user_access()
        for config_template in configurable_templates:
            variant_unlink = config_template.env.context.get(
                "unlink_from_variant", False
            )
            if variant_unlink:
                self -= config_template
        res = super(ProductTemplate, self).unlink()
        return res

    def copy(self, default=None):
        """Copy restrictions, config Steps and attribute lines
        ith product template"""
        if not default:
            default = {}
        self = self.with_context(check_constraint=False)
        res = super(ProductTemplate, self).copy(default=default)

        # Attribute lines
        attribute_line_dict = {}
        for line in res.attribute_line_ids:
            attribute_line_dict.update({line.attribute_id.id: line.id})

        # Restrictions
        for line in self.config_line_ids:
            old_restriction = line.domain_id
            new_restriction = old_restriction.copy()
            config_line_default = {
                "product_tmpl_id": res.id,
                "domain_id": new_restriction.id,
            }
            new_attribute_line_id = attribute_line_dict.get(
                line.attribute_line_id.attribute_id.id, False
            )
            if not new_attribute_line_id:
                continue
            config_line_default.update(
                {"attribute_line_id": new_attribute_line_id}
            )
            line.copy(config_line_default)

        # Config steps
        config_step_line_default = {"product_tmpl_id": res.id}
        for line in self.config_step_line_ids:
            new_attribute_line_ids = [
                attribute_line_dict.get(old_attr_line.attribute_id.id)
                for old_attr_line in line.attribute_line_ids
                if old_attr_line.attribute_id.id in attribute_line_dict
            ]
            if new_attribute_line_ids:
                config_step_line_default.update(
                    {"attribute_line_ids": [(6, 0, new_attribute_line_ids)]}
                )
            line.copy(config_step_line_default)
        return res

    def configure_product(self):
        """launches a product configurator wizard with a linked
        template in order to configure new product."""
        return self.with_context(
            product_tmpl_id_readonly=True
        ).create_config_wizard(click_next=False)

    def create_config_wizard(
        self,
        model_name="product.configurator",
        extra_vals=None,
        click_next=True,
    ):
        """create product configuration wizard
        - return action to launch wizard
        - click on next step based on value of click_next"""
        wizard_obj = self.env[model_name]
        wizard_vals = {"product_tmpl_id": self.id}
        if extra_vals:
            wizard_vals.update(extra_vals)
        wizard = wizard_obj.create(wizard_vals)
        if click_next:
            action = wizard.action_next_step()
        else:
            wizard_obj = wizard_obj.with_context(
                wizard_model=model_name,
                allow_preset_selection=True,
            )
            action = wizard_obj.get_wizard_action(wizard=wizard)
        return action

    @api.model
    def _check_config_group_rights(self):
        """Return True/False from system parameter
        - Signals access rights needs to check or not
        :Params: return : boolean"""
        ICPSudo = self.env["ir.config_parameter"].sudo()
        manager_product_configuration_settings = ICPSudo.get_param(
            "product_configurator.manager_product_configuration_settings"
        )
        return manager_product_configuration_settings

    @api.model
    def check_config_user_access(self):
        """Check user have access to perform action(create/write/delete)
        on configurable products"""
        if not self._check_config_group_rights():
            return True
        config_manager = self.env.user.has_group(
            "product_configurator.group_product_configurator_manager"
        )
        user_root = self.env.ref("base.user_root")
        user_admin = self.env.ref("base.user_admin")
        if config_manager or self.env.user.id in [user_root.id, user_admin.id] or self.env.su:
            return True
        raise ValidationError(
            _(
                "Sorry, you are not allowed to create/change this kind of "
                "document. For more information please contact your manager."
            )
        )

    @api.model
    def create(self, vals):
        """Patch for check access rights of user(configurable products)"""
        config_ok = vals.get("config_ok", False)
        if config_ok:
            self.check_config_user_access()
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        """Patch for check access rights of user(configurable products)"""
        change_config_ok = "config_ok" in vals
        configurable_templates = self.filtered(
            lambda template: template.config_ok
        )
        if change_config_ok or configurable_templates:
            self[:1].check_config_user_access()

        return super(ProductTemplate, self).write(vals)

    @api.constrains("config_line_ids")
    def _check_config_line_domain(self):
        attribute_line_ids = self.attribute_line_ids
        tmpl_value_ids = attribute_line_ids.mapped("value_ids")
        tmpl_attribute_ids = attribute_line_ids.mapped("attribute_id")
        error_message = False
        for domain_id in self.config_line_ids.mapped("domain_id"):
            domain_attr_ids = domain_id.domain_line_ids.mapped("attribute_id")
            domain_value_ids = domain_id.domain_line_ids.mapped("value_ids")
            invalid_value_ids = domain_value_ids - tmpl_value_ids
            invalid_attribute_ids = domain_attr_ids - tmpl_attribute_ids
            if not invalid_value_ids and not invalid_value_ids:
                continue
            if not error_message:
                error_message = _(
                    "Following Attribute/Value from restriction "
                    "are not present in template attributes/values. "
                    "Please make sure you are adding right restriction"
                )
            error_message += _("\nRestriction: %s") % (domain_id.name)
            error_message += (
                invalid_attribute_ids
                and _("\nAttribute/s: %s")
                % (", ".join(invalid_attribute_ids.mapped("name")))
                or ""
            )
            error_message += (
                invalid_value_ids
                and _("\nValue/s: %s\n")
                % (", ".join(invalid_value_ids.mapped("name")))
                or ""
            )
        if error_message:
            raise ValidationError(error_message)


class ProductProduct(models.Model):
    _inherit = "product.product"
    _rec_name = "config_name"

    def _get_conversions_dict(self):
        conversions = {"float": float, "integer": int}
        return conversions

    @api.constrains("product_template_attribute_value_ids")
    def _check_duplicate_product(self):
        """Check for prducts with same attribute values/custom values"""
        for product in self:
            if not product.config_ok:
                continue

            # At the moment, I don't have enough confidence with my
            # understanding of binary attributes, so will leave these
            # as not matching...
            # In theory, they should just work, if they are set to "non search"
            # in custom field def!
            # TODO: Check the logic with binary attributes
            config_session_obj = product.env["product.config.session"]
            ptav_ids = product.product_template_attribute_value_ids.mapped(
                "product_attribute_value_id"
            )
            duplicates = config_session_obj.search_variant(
                product_tmpl_id=product.product_tmpl_id,
                value_ids=ptav_ids.ids,
            ).filtered(lambda p: p.id != product.id)

            if duplicates:
                raise ValidationError(
                    _(
                        "Configurable Products cannot have duplicates "
                        "(identical attribute values)"
                    )
                )

    def _get_config_name(self):
        """Name for configured products
        :param: return : String"""
        self.ensure_one()
        return self.name

    def _get_mako_context(self, buf):
        """Return context needed for computing product name based
        on mako-tamplate define on it's product template"""
        self.ensure_one()
        ptav_ids = self.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id"
        )
        return Context(
            buf,
            product=self,
            attribute_values=ptav_ids,
            steps=self.product_tmpl_id.config_step_line_ids,
            template=self.product_tmpl_id,
        )

    def _get_mako_tmpl_name(self):
        """Compute and return product name based on mako-tamplate
        define on it's product template"""
        self.ensure_one()
        if self.mako_tmpl_name:
            try:
                mytemplate = Template(self.mako_tmpl_name or "")
                buf = StringIO()
                ctx = self._get_mako_context(buf)
                mytemplate.render_context(ctx)
                return buf.getvalue()
            except Exception:
                _logger.error(
                    _("Error while calculating mako product name: %s")
                    % self.display_name
                )
        return self.display_name

    @api.depends("product_template_attribute_value_ids.weight_extra")
    def _compute_product_weight_extra(self):
        for product in self:
            product.weight_extra = sum(
                product.mapped(
                    "product_template_attribute_value_ids.weight_extra"
                )
            )

    def _compute_product_weight(self):
        for product in self:
            if product.config_ok:
                tmpl_weight = product.product_tmpl_id.weight
                product.weight = tmpl_weight + product.weight_extra
            else:
                product.weight = product.weight_dummy

    def _search_product_weight(self, operator, value):
        return [("weight_dummy", operator, value)]

    def _inverse_product_weight(self):
        """Store weight in dummy field"""
        self.weight_dummy = self.weight

    config_name = fields.Char(
        string="Name", size=256, compute="_compute_config_name"
    )
    weight_extra = fields.Float(
        string="Weight Extra", compute="_compute_product_weight_extra"
    )
    weight_dummy = fields.Float(string="Manual Weight", digits="Stock Weight")
    weight = fields.Float(
        compute="_compute_product_weight",
        inverse="_inverse_product_weight",
        search="_search_product_weight",
        store=False,
    )

    # product preset
    config_preset_ok = fields.Boolean(string="Is Preset")

    def get_product_attribute_values_action(self):
        self.ensure_one()
        action = self.env.ref("product.product_attribute_value_action").read()[
            0
        ]
        value_ids = self.product_template_attribute_value_ids.ids
        action["domain"] = [("id", "in", value_ids)]
        context = safe_eval(
            action["context"], {"active_id": self.product_tmpl_id.id}
        )
        context.update({"active_id": self.product_tmpl_id.id})
        action["context"] = context
        return action

    def _compute_config_name(self):
        """ Compute the name of the configurable products and use template
            name for others"""
        for product in self:
            if product.config_ok:
                product.config_name = product._get_config_name()
            else:
                product.config_name = product.name

    def reconfigure_product(self):
        """launches a product configurator wizard with a linked
        template and variant in order to re-configure an existing product.
        It is essentially a shortcut to pre-fill configuration
        data of a variant"""
        self.ensure_one()

        extra_vals = {"product_id": self.id}
        return self.product_tmpl_id.create_config_wizard(extra_vals=extra_vals)

    @api.model
    def check_config_user_access(self, mode):
        """Check user have access to perform action(create/write/delete)
        on configurable products"""
        if not self.env["product.template"]._check_config_group_rights():
            return True
        config_manager = self.env.user.has_group(
            "product_configurator.group_product_configurator_manager"
        )
        config_user = self.env.user.has_group(
            "product_configurator.group_product_configurator"
        )
        user_root = self.env.ref("base.user_root")
        user_admin = self.env.ref("base.user_admin")
        if (
            config_manager
            or (config_user and mode not in ["delete"])
            or self.env.user.id in [user_root.id, user_admin.id]
        ):
            return True
        raise ValidationError(
            _(
                "Sorry, you are not allowed to create/change this kind of "
                "document. For more information please contact your manager."
            )
        )

    def unlink(self):
        """- Signal unlink from product variant through context so
        removal can be stopped for configurable templates
        - check access rights of user(configurable products)"""
        config_product = any(p.config_ok for p in self)
        if config_product:
            self.env["product.product"].check_config_user_access(mode="delete")
        ctx = dict(self.env.context, unlink_from_variant=True)
        self.env.context = ctx
        return super(ProductProduct, self).unlink()

    @api.model
    def create(self, vals):
        """Patch for check access rights of user(configurable products)
        """
        config_ok = vals.get("config_ok", False)
        if config_ok:
            self.check_config_user_access(mode="create")
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        """Patch for check access rights of user(configurable products)
        """
        change_config_ok = "config_ok" in vals
        configurable_products = self.filtered(
            lambda product: product.config_ok
        )
        if change_config_ok or configurable_products:
            self[:1].check_config_user_access(mode="write")

        return super(ProductProduct, self).write(vals)

    def get_products_with_session(self, config_session_map=None):
        products_to_update = self.env['product.product']
        if not config_session_map:
            return products_to_update
        config_session_products = self.filtered(lambda p: p.config_ok)
        for cfg_product in config_session_products:
            if cfg_product.id not in config_session_map.keys():
                continue
            product_session = self.env['product.config.session'].browse(
                config_session_map.get(cfg_product.id)
            )
            if (not product_session.exists() or
                    product_session.product_id != cfg_product):
                continue
            products_to_update += cfg_product
        return products_to_update

    @api.depends_context('product_sessions')
    def _compute_product_price(self):
        session_map = self.env.context.get('product_sessions', ())
        if isinstance(session_map, tuple):
            session_map = dict(session_map)
        config_session_products = self.get_products_with_session(
            session_map.copy()
        )
        standard_products = self - config_session_products
        for cfg_product in config_session_products:
            product_session = self.env['product.config.session'].browse(
                session_map.get(cfg_product.id)
            )
            cfg_product.price = product_session.price
        super(ProductProduct, standard_products)._compute_product_price()

    def price_compute(self, price_type,
                      uom=False, currency=False, company=False):
        standard_products = self.filtered(lambda a: not a.config_ok)
        res = {}
        if standard_products:
            res = super(ProductProduct, standard_products).price_compute(
                price_type, uom=uom,
                currency=currency, company=company
            )
        config_products = self - standard_products
        for config_product in config_products:
            res[config_product.id] = config_product.price
        return res
