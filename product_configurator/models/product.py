from lxml import etree

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from mako.template import Template
from mako.runtime import Context
from odoo.tools.safe_eval import safe_eval
from io import StringIO
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.one
    @api.depends('product_variant_ids.product_tmpl_id')
    def _compute_product_variant_count(self):
        """For configurable products return the number of variants configured or 1
        as many views and methods trigger only when a template has at least one
        variant attached. Since we create them from the template we should have
        access to them always"""
        super(ProductTemplate, self)._compute_product_variant_count()
        if self.config_ok and not self.product_variant_count:
            self.product_variant_count = 1

    @api.multi
    @api.depends('attribute_line_ids.value_ids')
    def _compute_template_attr_vals(self):
        for product_tmpl in self.filtered(lambda t: t.config_ok):
            value_ids = product_tmpl.attribute_line_ids.mapped('value_ids')
            product_tmpl.attribute_line_val_ids = value_ids

    @api.multi
    @api.constrains('attribute_line_ids', 'attribute_value_line_ids')
    def check_attr_value_ids(self):
        for product_tmpl in self:
            attr_val_lines = product_tmpl.attribute_value_line_ids
            attr_val_ids = attr_val_lines.mapped('value_ids')
            print("$$$$$$$$$$$$$$$$$$$$$$ ",attr_val_lines, attr_val_ids, product_tmpl.attribute_line_val_ids)
            if not attr_val_ids <= product_tmpl.attribute_line_val_ids:
                raise ValidationError(
                    _("All attribute values used in attribute value lines "
                      "must be defined in the attribute lines of the template")
                )

    @api.multi
    @api.constrains('attribute_value_line_ids')
    def _validate_unique_config(self):
        """Check for duplicate configurations for the same attribute value"""
        attr_val_line_vals = self.attribute_value_line_ids.read(
            ['value_id', 'value_ids'], load=False
        )
        attr_val_line_vals = [
            (l['value_id'], tuple(l['value_ids'])) for l in attr_val_line_vals
        ]
        if len(set(attr_val_line_vals)) != len(attr_val_line_vals):
            raise ValidationError(
                _('You cannot have a duplicate configuration for the '
                  'same value')
            )

    config_ok = fields.Boolean(string='Can be Configured')

    config_line_ids = fields.One2many(
        comodel_name='product.config.line',
        inverse_name='product_tmpl_id',
        string="Attribute Dependencies",
        copy=False
    )

    config_image_ids = fields.One2many(
        comodel_name='product.config.image',
        inverse_name='product_tmpl_id',
        string='Configuration Images',
        copy=True
    )

    attribute_value_line_ids = fields.One2many(
        comodel_name='product.attribute.value.line',
        inverse_name='product_tmpl_id',
        string="Attribute Value Lines",
        copy=True
    )

    attribute_line_val_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        compute='_compute_template_attr_vals',
        store=False
    )

    config_step_line_ids = fields.One2many(
        comodel_name='product.config.step.line',
        inverse_name='product_tmpl_id',
        string='Configuration Lines',
        copy=False
    )

    mako_tmpl_name = fields.Text(
        string='Variant name',
        help="Generate Name based on Mako Template",
        copy=True
    )

    @api.multi
    def get_product_attribute_values_action(self):
        self.ensure_one()
        action = self.env.ref(
            'product.product_attribute_value_action').read()[0]
        value_ids = self.attribute_line_ids.mapped('value_ids').ids
        action['domain'] = [('id', 'in', value_ids)]
        context = safe_eval(action['context'], {'active_id': self.id})
        context.update({'active_id': self.id})
        action['context'] = context
        return action

    @api.multi
    @api.constrains('attribute_line_ids', 'attribute_line_ids.default_val')
    def _check_default_values(self):
        """Validate default values set on the product template"""
        default_val_ids = self.attribute_line_ids.filtered(
            lambda l: l.default_val).mapped('default_val').ids

        # TODO: Remove if cond when PR with raise error on github is merged
        cfg_session_obj = self.env['product.config.session']
        valid_conf = cfg_session_obj.validate_configuration(
            value_ids=default_val_ids, product_tmpl_id=self.id, final=False
        )
        if not valid_conf:
            raise ValidationError(
                _('Default values provided generate an invalid configuration')
            )

    @api.multi
    @api.constrains('config_line_ids')
    def _check_default_value_domains(self):
        try:
            self._check_default_values()
        except ValidationError:
            raise ValidationError(
                _('Restrictions added make the current default values '
                  'generate an invalid configuration')
            )

    @api.multi
    def toggle_config(self):
        for record in self:
            record.config_ok = not record.config_ok

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

    @api.multi
    def copy(self, default=None):
        new_products = self.env['product.template']
        for product in self:
            res = super(ProductTemplate, self).copy(default=default)

            print(res.id)
            # default = {'product_tmpl_id': res.id}
            attribute_line_dict = {}
            print("self.attribute_line_ids ",self.attribute_line_ids, self.config_line_ids)
            for line in self.attribute_line_ids:
                default = {'product_tmpl_id': res.id}
                new_line = line.copy(default)
                attribute_line_dict.update({line.id: new_line.id})

            print("Qqqqqqqqqqqqqqqqqqqqqqq",attribute_line_dict)

            for line in self.config_line_ids:
                old_restriction = line.domain_id
                new_restriction = old_restriction.copy()
                default = {'product_tmpl_id': res.id, 'domain_id': new_restriction.id}
                new_attribute_line_id = attribute_line_dict.get(line.id, False)
                if new_attribute_line_id:
                    default.update({'attribute_line_id': new_attribute_line_id})
                line.copy(default)

            for line in self.config_step_line_ids:
                default = {'product_tmpl_id': res.id}
                new_attribute_line_ids = [
                    attribute_line_dict.get(old_attr_line.id)
                    for old_attr_line in line.attribute_line_ids
                ]
                if new_attribute_line_ids:
                    default.update({'attribute_line_ids': [(6, 0, new_attribute_line_ids)]})
                line.copy(default)

            new_products += res
        return new_products

    @api.multi
    def configure_product(self):
        return self.create_config_wizard()

    def create_config_wizard(self, model_name="product.configurator",
                             extra_vals=None, click_next=True):
        """create product configuration wizard
        - return action to launch wizard
        - click on next step based on value of click_next"""

        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'product.configurator',
            'name': "Product Configurator",
            'view_mode': 'form',
            'target': 'new',
            'context': dict(
                self.env.context,
                wizard_model='product.configurator',
            ),
        }

        wizard_obj = self.env[model_name]
        wizard_vals = {
            'product_tmpl_id': self.id
        }
        if extra_vals:
            wizard_vals.update(extra_vals)
        wizard = wizard_obj.create(wizard_vals)
        if click_next:
            action = wizard.action_next_step()
        return action


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _rec_name = 'config_name'

    def _get_conversions_dict(self):
        conversions = {
            'float': float,
            'int': int
        }
        return conversions

    @api.constrains('attribute_value_ids')
    def _check_duplicate_product(self):
        if not self.config_ok:
            return None

        # At the moment, I don't have enough confidence with my understanding
        # of binary attributes, so will leave these as not matching...
        # In theory, they should just work, if they are set to "non search"
        # in custom field def!
        # TODO: Check the logic with binary attributes
        if not self.value_custom_ids.filtered(lambda cv: cv.attachment_ids):
            config_session_obj = self.env['product.config.session']
            custom_vals = {
                cv.attribute_id.id: cv.value
                for cv in self.value_custom_ids
            }
            duplicates = config_session_obj.search_variant(
                product_tmpl_id=self.product_tmpl_id.id,
                value_ids=self.attribute_value_ids.ids,
                custom_vals=custom_vals
            ).filtered(lambda p: p.id != self.id)

            if duplicates:
                raise ValidationError(
                    _("Configurable Products cannot have duplicates "
                      "(identical attribute values)")
                )

    @api.model
    def _get_config_name(self):
        return self.name

    @api.model
    def _get_mako_context(self, buf):
        return Context(
            buf, product=self,
            attribute_values=self.attribute_value_ids,
            steps=self.product_tmpl_id.config_step_line_ids,
            template=self.product_tmpl_id)

    @api.model
    def _get_mako_tmpl_name(self):
        if self.mako_tmpl_name:
            try:
                mytemplate = Template(self.mako_tmpl_name or '')
                buf = StringIO()
                ctx = self._get_mako_context(buf)
                mytemplate.render_context(ctx)
                return buf.getvalue()
            except Exception:
                _logger.error(
                    _("Error while calculating mako product name: %s") %
                    self.display_name)
        return self.display_name

    @api.depends('attribute_value_ids.price_ids.weight_extra',
                 'attribute_value_ids.price_ids.product_tmpl_id')
    def _compute_product_weight_extra(self):
        for product in self:
            weight_extra = 0.0
            attr_prices = product.mapped('attribute_value_ids.price_ids')
            for attribute_price in attr_prices:
                if attribute_price.product_tmpl_id == product.product_tmpl_id:
                    weight_extra += attribute_price.weight_extra
            product.weight_extra = weight_extra

    @api.depends('product_tmpl_id.weight', 'weight_extra')
    def _compute_product_weight(self):
        for product in self:
            tmpl_weight = product.product_tmpl_id.weight
            product.weight = tmpl_weight + product.weight_extra

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
    price_extra = fields.Float(
        compute='_compute_product_price_extra',
        string='Variant Extra Price',
        help="This is the sum of the extra price of all attributes",
        digits=dp.get_precision('Product Price')
    )
    weight_extra = fields.Float(
        string='Weight Extra',
        compute='_compute_product_weight_extra'
    )

    weight = fields.Float(compute='_compute_product_weight')

    @api.multi
    def get_product_attribute_values_action(self):
        self.ensure_one()
        action = self.env.ref(
            'product.product_attribute_value_action').read()[0]
        value_ids = self.attribute_value_ids.ids
        action['domain'] = [('id', 'in', value_ids)]
        context = safe_eval(
            action['context'],
            {'active_id': self.product_tmpl_id.id}
        )
        context.update({'active_id': self.product_tmpl_id.id})
        action['context'] = context
        return action

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
                product.config_name = product._get_config_name()
            else:
                product.config_name = product.name

    @api.multi
    def reconfigure_product(self):
        """ Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure an existing product.
        It is essentially a shortcut to pre-fill configuration
        data of a variant"""

        extra_vals = {
            'product_id': self.id,
        }
        return self.product_tmpl_id.create_config_wizard(
            extra_vals=extra_vals)
