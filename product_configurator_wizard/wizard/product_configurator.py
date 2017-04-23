# -*- coding: utf-8 -*-

from lxml import etree

from odoo.osv import orm
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class FreeSelection(fields.Selection):

    def convert_to_cache(self, value, record, validate=True):
        return super(FreeSelection, self).convert_to_cache(
            value=value, record=record, validate=False)


class ProductConfigurator(models.TransientModel):
    _name = 'product.configurator'
    _inherits = {'product.config.session': 'config_session'}

    # Prefix for the dynamicly injected fields
    field_prefix = '__attribute-'
    custom_field_prefix = '__custom-'

    # TODO: Since the configuration process can take a bit of time
    # depending on complexity and AFK time we must increase the lifespan
    # of this TransientModel life

    @api.multi
    @api.depends('product_tmpl_id', 'value_ids', 'custom_value_ids')
    def _compute_cfg_image(self):
        # TODO: Update when allowing custom values to influence image
        product_tmpl = self.product_tmpl_id.with_context(bin_size=False)
        img_obj = product_tmpl.get_config_image_obj(self.value_ids.ids)
        self.product_img = img_obj.image

    # TODO: We could use a m2o instead of a monkeypatched select field but
    # adding new steps should be trivial via custom development
    @api.multi
    def get_state_selection(self):
        """Get the states of the wizard using standard values and optional
        configuration steps set on the product.template via
        config_step_line_ids"""

        steps = [('select', "Select Template")]

        # Get the wizard id from context set via action_next_step method
        wizard_id = self.env.context.get('wizard_id')

        if not wizard_id:
            return steps

        wiz = self.browse(wizard_id)

        open_lines = wiz.product_tmpl_id.get_open_step_lines(
            wiz.value_ids.ids)

        if open_lines:
            open_steps = open_lines.mapped(
                lambda x: (str(x.id), x.config_step_id.name)
            )
            steps = open_steps if wiz.product_id else steps + open_steps
        else:
            steps.append(('configure', 'Configure'))
        return steps

    @api.onchange('product_tmpl_id')
    def onchange_product_tmpl(self):
        template = self.product_tmpl_id
        self.config_step_ids = template.config_step_line_ids.mapped(
            'config_step_id')
        if self.value_ids:
            # TODO: Add confirmation button an delete cfg session
            raise Warning(
                _('Changing the product template while having an active '
                  'configuration will erase reset/clear all values')
            )

    def get_onchange_domains(self, values, cfg_val_ids):
        """Generate domains to be returned by onchange method in order
        to restrict the availble values of dynamically inserted fields

        :param values: values argument passed to onchance wrapper
        :cfg_val_ids: current configuration passed as a list of value_ids
        (usually in the form of db value_ids + interface value_ids)

        :returns: a dictionary of domains returned by onchance method
        """
        domains = {}
        for line in self.product_tmpl_id.attribute_line_ids.sorted():
            field_name = self.field_prefix + str(line.attribute_id.id)

            if field_name not in values:
                continue

            vals = values[field_name]

            # get available values
            avail_ids = self.product_tmpl_id.values_available(
                line.value_ids.ids, cfg_val_ids)
            domains[field_name] = [('id', 'in', avail_ids)]

            # Include custom value in the domain if attr line permits it
            if line.custom:
                custom_ext_id = 'product_configurator.custom_attribute_value'
                custom_val = self.env.ref(custom_ext_id)
                domains[field_name][0][2].append(custom_val.id)
                if line.multi and vals and custom_val.id in vals[0][2]:
                    continue
        return domains

    def get_form_vals(self, dynamic_fields, domains):
        """Generate a dictionary to return new values via onchange method.
        Domains hold the values available, this method enforces these values
        if a selection exists in the view that is not available anymore.

        :param dynamic_fields: Dictionary with the current {dynamic_field: val}
        :param domains: Odoo domains restricting attribute values

        :returns vals: Dictionary passed to {'value': vals} by onchange method
        """
        vals = {}

        dynamic_fields = {k: v for k, v in dynamic_fields.iteritems() if v}

        for k, v in dynamic_fields.iteritems():
            if not v:
                continue
            available_val_ids = domains[k][0][2]
            if isinstance(v, list):
                value_ids = list(set(v[0][2]) & set(available_val_ids))
                dynamic_fields.update({k: value_ids})
                vals[k] = [[6, 0, value_ids]]
            elif v not in available_val_ids:
                dynamic_fields.update({k: None})
                vals[k] = None

        product_img = self.product_tmpl_id.get_config_image_obj(
            dynamic_fields.values())

        vals.update(product_img=product_img.image)

        return vals

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        """ Override the onchange wrapper to return domains to dynamic
        fields as onchange isn't triggered for non-db fields
        """
        field_type = type(field_name)

        if field_type == list or not field_name.startswith(self.field_prefix):
            res = super(ProductConfigurator, self).onchange(
                values, field_name, field_onchange)
            return res

        cfg_vals = self.value_ids

        view_val_ids = set()
        view_attribute_ids = set()

        try:
            cfg_step_id = int(self.state)
            cfg_step = self.product_tmpl_id.config_step_line_ids.filtered(
                lambda x: x.id == cfg_step_id)
        except:
            cfg_step = self.env['product.config.step.line']

        dynamic_fields = {
            k: v for k, v in values.iteritems() if k.startswith(
                self.field_prefix)
        }

        # Get the unstored values from the client view
        for k, v in dynamic_fields.iteritems():
            attr_id = int(k.split(self.field_prefix)[1])
            line_attributes = cfg_step.attribute_line_ids.mapped(
                'attribute_id')
            if not cfg_step or attr_id in line_attributes.ids:
                view_attribute_ids.add(attr_id)
            else:
                continue
            if not v:
                continue
            if isinstance(v, list):
                view_val_ids |= set(v[0][2])
            elif isinstance(v, int):
                view_val_ids.add(v)

        # Clear all DB values belonging to attributes changed in the wizard
        cfg_vals = cfg_vals.filtered(
            lambda v: v.attribute_id.id not in view_attribute_ids
        )

        # Combine database values with wizard values
        cfg_val_ids = cfg_vals.ids + list(view_val_ids)

        domains = self.get_onchange_domains(values, cfg_val_ids)
        vals = self.get_form_vals(dynamic_fields, domains)
        return {'value': vals, 'domain': domains}

    attribute_line_ids = fields.One2many(
        comodel_name='product.attribute.line',
        related='product_tmpl_id.attribute_line_ids',
        string="Attributes",
        readonly=True,
        store=False
    )
    config_step_ids = fields.Many2many(
        comodel_name='product.config.step',
        relation="product_config_config_steps_rel",
        column1='config_wiz_id',
        column2='config_step_id',
        string="Configuration Steps",
        readonly=True,
        store=False
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        readonly=True,
        string='Product Variant',
        help='Set only when re-configuring a existing variant'
    )
    product_img = fields.Binary(
        compute='_compute_cfg_image',
        readonly=True
    )
    state = FreeSelection(
        selection='get_state_selection',
        default='select',
        string='State',
    )
    order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        readonly=True,
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """ Artificially inject fields which are dynamically created using the
        attribute_ids on the product.template as reference"""
        res = super(ProductConfigurator, self).fields_get(
            allfields=allfields,
            attributes=attributes
        )

        wizard_id = self.env.context.get('wizard_id')

        # If wizard_id is not defined in the context then the wizard was just
        # launched and is not stored in the database yet
        if not wizard_id:
            return res

        # Get the wizard object from the database
        wiz = self.browse(wizard_id)
        active_step_id = wiz.state

        # If the product template is not set it is still at the 1st step
        if not wiz.product_tmpl_id:
            return res

        cfg_step_lines = wiz.product_tmpl_id.config_step_line_ids

        try:
            # Get only the attribute lines for the next step if defined
            active_step_line = cfg_step_lines.filtered(
                lambda l: l.id == int(active_step_id))
            if active_step_line:
                attribute_lines = active_step_line.attribute_line_ids
            else:
                attribute_lines = wiz.product_tmpl_id.attribute_line_ids
        except:
            # If no configuration steps exist then get all attribute lines
            attribute_lines = wiz.product_tmpl_id.attribute_line_ids

        attribute_lines = wiz.product_tmpl_id.attribute_line_ids

        # Generate relational fields with domains restricting values to
        # the corresponding attributes

        # Default field attributes
        default_attrs = {
            'company_dependent': False,
            'depends': (),
            'groups': False,
            'readonly': False,
            'manual': False,
            'required': False,
            'searchable': False,
            'store': False,
            'translate': False,
        }

        for line in attribute_lines:
            attribute = line.attribute_id
            value_ids = line.value_ids.ids

            value_ids = wiz.product_tmpl_id.values_available(
                value_ids, wiz.value_ids.ids)

            # If attribute lines allows custom values add the
            # generic "Custom" attribute.value to the list of options
            if line.custom:
                custom_ext_id = 'product_configurator.custom_attribute_value'
                custom_val = self.env.ref(custom_ext_id)
                value_ids.append(custom_val.id)

                # Set default field type
                field_type = 'char'
                field_types = self.env['ir.model.fields']._get_field_types()

                if attribute.custom_type:
                    custom_type = line.attribute_id.custom_type
                    # TODO: Rename int to integer in values
                    if custom_type == 'int':
                        field_type = 'integer'
                    elif custom_type in [f[0] for f in field_types]:
                        field_type = custom_type

                # TODO: Implement custom string on custom attribute
                res[self.custom_field_prefix + str(attribute.id)] = dict(
                    default_attrs,
                    string="Custom",
                    type=field_type,
                    sequence=line.sequence,
                )

            # Add the dynamic field to the resultset using the convention
            # "__attribute-DBID" to later identify and extract it
            res[self.field_prefix + str(attribute.id)] = dict(
                default_attrs,
                type='many2many' if line.multi else 'many2one',
                domain=[('id', 'in', value_ids)],
                string=line.attribute_id.name,
                relation='product.attribute.value',
                sequence=line.sequence,
            )

        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Generate view dynamically using attributes stored on the
        product.template"""
        res = super(ProductConfigurator, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu
        )

        wizard_id = self.env.context.get('wizard_id')

        if res.get('type') != 'form' or not wizard_id:
            return res

        wiz = self.browse(wizard_id)

        # Get updated fields including the dynamic ones
        fields = self.fields_get()
        dynamic_fields = {
            k: v for k, v in fields.iteritems() if k.startswith(
                self.field_prefix) or k.startswith(self.custom_field_prefix)
        }

        res['fields'].update(dynamic_fields)
        mod_view = self.add_dynamic_fields(res, dynamic_fields, wiz)

        # Update result dict from super with modified view
        res.update({'arch': etree.tostring(mod_view)})

        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        """ Create the configuration view using the dynamically generated
            fields in fields_get()
        """
        try:
            # Search for view container hook and add dynamic view and fields
            xml_view = etree.fromstring(res['arch'])
            xml_static_form = xml_view.xpath(
                "//group[@name='static_form']")[0]
            xml_dynamic_form = etree.Element(
                'group',
                colspan='3',
                name='dynamic_form'
            )
            xml_parent = xml_static_form.getparent()
            xml_parent.insert(xml_parent.index(
                xml_static_form) + 1, xml_dynamic_form)
            xml_dynamic_form = xml_view.xpath(
                "//group[@name='dynamic_form']")[0]
        except Exception:
            raise Warning(
                _('There was a problem rendering the view '
                  '(dynamic_form not found)')
            )

        # Get all dynamic fields inserted via fields_get method
        attr_lines = wiz.product_tmpl_id.attribute_line_ids.sorted()

        # Loop over the dynamic fields and add them to the view one by one
        for attr_line in attr_lines:

            attribute_id = attr_line.attribute_id.id
            field_name = self.field_prefix + str(attribute_id)
            custom_field = self.custom_field_prefix + str(attribute_id)

            # Check if the attribute line has been added to the db fields
            if field_name not in dynamic_fields:
                continue

            config_steps = wiz.product_tmpl_id.config_step_line_ids.filtered(
                lambda x: attr_line in x.attribute_line_ids)

            # attrs property for dynamic fields
            attrs = {
                'readonly': ['|'],
                'required': [],
                'invisible': ['|']
            }

            if config_steps:
                cfg_step_ids = [str(id) for id in config_steps.ids]
                attrs['invisible'].append(('state', 'not in', cfg_step_ids))
                attrs['readonly'].append(('state', 'not in', cfg_step_ids))

                # If attribute is required make it so only in the proper step
                if attr_line.required:
                    attrs['required'].append(('state', 'in', cfg_step_ids))

            if attr_line.custom:
                pass
                # TODO: Implement restrictions for ranges

            config_lines = wiz.product_tmpl_id.config_line_ids
            dependencies = config_lines.filtered(
                lambda cl: cl.attribute_line_id == attr_line)

            # If an attribute field depends on another field from the same
            # configuration step then we must use attrs to enable/disable the
            # required and readonly depending on the value entered in the
            # dependee

            if attr_line.value_ids <= dependencies.mapped('value_ids'):
                attr_depends = {}
                domain_lines = dependencies.mapped('domain_id.domain_line_ids')
                for domain_line in domain_lines:
                    attr_id = domain_line.attribute_id.id
                    attr_field = self.field_prefix + str(attr_id)
                    attr_lines = wiz.product_tmpl_id.attribute_line_ids
                    # If the fields it depends on are not in the config step
                    if config_steps and str(attr_line.id) != wiz.state:
                        continue
                    if attr_field not in attr_depends:
                        attr_depends[attr_field] = set()
                    if domain_line.condition == 'in':
                        attr_depends[attr_field] |= set(
                            domain_line.value_ids.ids)
                    elif domain_line.condition == 'not in':
                        val_ids = attr_lines.filtered(
                            lambda l: l.attribute_id.id == attr_id).value_ids
                        val_ids = val_ids - domain_line.value_ids
                        attr_depends[attr_field] |= set(val_ids.ids)

                for dependee_field, val_ids in attr_depends.iteritems():
                    if not val_ids:
                        continue
                    attrs['readonly'].append(
                        (dependee_field, 'not in', list(val_ids)))
                    attrs['required'].append(
                        (dependee_field, 'in', list(val_ids)))

            # Create the new field in the view
            node = etree.Element(
                "field",
                name=field_name,
                on_change="onchange_attribute_value(%s, context)" % field_name,
                default_focus="1" if attr_line == attr_lines[0] else "0",
                attrs=str(attrs),
                context="{'show_attribute': False}",
                options=str({
                    'no_create': True,
                    'no_create_edit': True,
                    'no_open': True
                })
            )

            if attr_line.required and not config_steps:
                node.attrib['required'] = '1'

            field_type = dynamic_fields[field_name].get('type')
            if field_type == 'many2many':
                node.attrib['widget'] = 'many2many_tags'

            # Apply the modifiers (attrs) on the newly inserted field in the
            # arch and add it to the view
            orm.setup_modifiers(node)
            xml_dynamic_form.append(node)

            if attr_line.custom and custom_field in dynamic_fields:
                widget = ''
                custom_ext_id = 'product_configurator.custom_attribute_value'
                custom_option_id = self.env.ref(custom_ext_id).id

                if field_type == 'many2many':
                    field_val = [(6, False, [custom_option_id])]
                else:
                    field_val = custom_option_id

                attrs['readonly'] += [(field_name, '!=', field_val)]
                attrs['invisible'] += [(field_name, '!=', field_val)]
                attrs['required'] += [(field_name, '=', field_val)]

                if config_steps:
                    attrs['required'] += [('state', 'in', cfg_step_ids)]

                # TODO: Add a field2widget mapper
                if attr_line.attribute_id.custom_type == 'color':
                    widget = 'color'
                node = etree.Element(
                    "field",
                    name=custom_field,
                    attrs=str(attrs),
                    widget=widget
                )
                orm.setup_modifiers(node)
                xml_dynamic_form.append(node)

        return xml_view

    @api.model
    def create(self, vals):
        """Sets the configuration values of the product_id if given (if any).
        This is used in reconfiguration of a existing variant"""
        vals.update(user_id=self.env.uid)

        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals.update({
                'product_tmpl_id': product.product_tmpl_id.id,
                'value_ids': [(6, 0, product.attribute_value_ids.ids)]
            })
            custom_vals = []
            for val in product.value_custom_ids:
                custom_vals.append((0, 0, {
                    'attribute_id': val.attribute_id.id,
                    'value': val.value,
                    'attachment_ids': [(6, 0, val.attachment_ids.ids)],
                }))
            if custom_vals:
                vals.update({'custom_value_ids': custom_vals})
        return super(ProductConfigurator, self).create(vals)

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Remove dynamic fields from the fields list and update the
        returned values with the dynamic data stored in value_ids"""
        attr_vals = [f for f in fields if f.startswith(self.field_prefix)]
        custom_attr_vals = [
            f for f in fields if f.startswith(self.custom_field_prefix)
        ]

        dynamic_fields = attr_vals + custom_attr_vals
        fields = [f for f in fields if f not in dynamic_fields]

        custom_ext_id = 'product_configurator.custom_attribute_value'
        custom_val = self.env.ref(custom_ext_id)
        dynamic_vals = {}

        res = super(ProductConfigurator, self).read(fields=fields, load=load)

        if not dynamic_fields:
            return res

        for attr_line in self.product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            field_name = self.field_prefix + str(attr_id)

            if field_name not in dynamic_fields:
                continue

            custom_field_name = self.custom_field_prefix + str(attr_id)
            custom_vals = self.custom_value_ids.filtered(
                lambda x: x.attribute_id.id == attr_id)
            vals = attr_line.value_ids.filtered(
                lambda v: v in self.value_ids)

            if not attr_line.custom and not vals:
                continue

            if attr_line.custom and custom_vals:
                dynamic_vals.update({
                    field_name: custom_val.id,
                })
                if attr_line.attribute_id.custom_type == 'binary':
                    dynamic_vals.update({
                        custom_field_name: custom_vals.eval()
                    })
                else:
                    dynamic_vals.update({
                        custom_field_name: custom_vals.eval()
                    })
            elif attr_line.multi:
                dynamic_vals = {field_name: [[6, 0, vals.ids]]}
            else:
                try:
                    vals.ensure_one()
                    dynamic_vals = {field_name: vals.id}
                except:
                    continue
            res[0].update(dynamic_vals)
        return res

    @api.multi
    def write(self, vals):
        """Prevent database storage of dynamic fields and instead write values
        to database persistent value_ids field"""

        # Get current database value_ids (current configuration)

        custom_ext_id = 'product_configurator.custom_attribute_value'
        custom_val = self.env.ref(custom_ext_id)

        attr_val_dict = {}
        custom_val_dict = {}

        for attr_line in self.product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            field_name = self.field_prefix + str(attr_id)
            custom_field_name = self.custom_field_prefix + str(attr_id)

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
                    raise Warning(
                        _('An error occursed while parsing value for '
                          'attribute %s' % attr_line.attribute_id.name)
                    )
                attr_val_dict.update({
                    attr_id: field_val
                })
                # Ensure there is no custom value stored if we have switched
                # from custom value to selected attribute value.
                if attr_line.custom:
                    custom_val_dict.update({attr_id: False})
            elif attr_line.custom:
                val = vals.get(custom_field_name, False)
                if attr_line.attribute_id.custom_type == 'binary':
                    # TODO: Add widget that enables multiple file uploads
                    val = [{
                        'name': 'custom',
                        'datas': vals[custom_field_name]
                    }]
                custom_val_dict.update({
                    attr_id: val
                })
                # Ensure there is no standard value stored if we have switched
                # from selected value to custom value.
                attr_val_dict.update({attr_id: False})

            # Remove dynamic field from value list to prevent error
            if field_name in vals:
                del vals[field_name]
            if custom_field_name in vals:
                del vals[custom_field_name]

        self.config_session.update_config(attr_val_dict, custom_val_dict)
        res = super(ProductConfigurator, self).write(vals)
        return res

    @api.multi
    def unlink(self):
        """Remove parent model as polymorphic inheritance unlinks inheriting
           model with the parent"""
        return self.mapped('config_session').unlink()

    @api.multi
    def action_next_step(self):
        """Proceeds to the next step of the configuration process. This usually
        implies the next configuration step (if any) defined via the
        config_step_line_ids on the product.template.

        More importantly it sets metadata on the context
        variable so the fields_get and fields_view_get methods can generate the
        appropriate dynamic content"""

        wizard_action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=self.id,
            ),
            'target': 'new',
            'res_id': self.id,
        }

        if not self.product_tmpl_id:
            return wizard_action

        cfg_step_lines = self.product_tmpl_id.config_step_line_ids

        if not cfg_step_lines:
            if self.value_ids:
                return self.action_config_done()
            else:
                self.state = 'configure'
                return wizard_action

        try:
            cfg_step_line_id = int(self.state)
        except:
            cfg_step_line_id = None

        active_cfg_line_id = cfg_step_lines.filtered(
            lambda x: x.id == cfg_step_line_id).id

        adjacent_steps = self.product_tmpl_id.get_adjacent_steps(
            self.value_ids.ids, active_cfg_line_id)

        next_step = adjacent_steps.get('next_step')

        if next_step:
            self.state = next_step.id
        else:
            return self.action_config_done()

        return wizard_action

    @api.multi
    def action_previous_step(self):
        """Proceeds to the next step of the configuration process. This usually
    implies the next configuration step (if any) defined via the
    config_step_line_ids on the product.template."""

        wizard_action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'name': "Configure Product",
            'view_mode': 'form',
            'context': dict(
                self.env.context,
                wizard_id=self.id,
            ),
            'target': 'new',
            'res_id': self.id,
        }

        cfg_step_lines = self.product_tmpl_id.config_step_line_ids

        if not cfg_step_lines:
            return wizard_action

        try:
            cfg_step_line_id = int(self.state)
            active_cfg_line_id = cfg_step_lines.filtered(
                lambda x: x.id == cfg_step_line_id).id
        except:
            active_cfg_line_id = None

        adjacent_steps = self.product_tmpl_id.get_adjacent_steps(
            self.value_ids.ids, active_cfg_line_id)

        previous_step = adjacent_steps.get('previous_step')

        if previous_step:
            self.state = previous_step.id
        else:
            self.state = 'select'

        return wizard_action

    def _extra_line_values(self, so, product, new=True):
        """ Hook to allow custom line values to be put on the newly
        created or edited lines."""
        vals = {}
        if new:
            vals.update({
                'name': product.display_name,
                'product_uom': product.uom_id.id,
            })
        return vals

    @api.multi
    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        custom_vals = {
            l.attribute_id.id:
                l.value or l.attachment_ids for l in self.custom_value_ids
        }

        # This try except is too generic.
        # The create_variant routine could effectively fail for
        # a large number of reasons, including bad programming.
        # It should be refactored.
        # In the meantime, at least make sure that a validation
        # error legitimately raised in a nested routine
        # is passed through.
        try:
            variant = self.product_tmpl_id.create_get_variant(
                self.value_ids.ids, custom_vals)
        except ValidationError:
            raise
        except:
            raise ValidationError(
                _('Invalid configuration! Please check all '
                  'required steps and fields.')
            )

        so = self.env['sale.order'].browse(self.env.context.get('active_id'))

        line_vals = {'product_id': variant.id}
        line_vals.update(self._extra_line_values(
            self.order_line_id.order_id or so, variant, new=True)
        )

        if self.order_line_id:
            self.order_line_id.write(line_vals)
        else:
            so.write({'order_line': [(0, 0, line_vals)]})

        self.unlink()
        return


class ProductConfiguratorCustomValue(models.TransientModel):
    _name = 'product.configurator.custom.value'

    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment',
        column1='config_attachment',
        column2='attachment_id',
        string='Attachments',
    )
    attribute_id = fields.Many2one(
        string='Attribute',
        comodel_name='product.attribute',
        required=True
    )
    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        related='wizard_id.create_uid',
        required=True
    )
    value = fields.Char(
        string='Value'
    )
    wizard_id = fields.Many2one(
        comodel_name='product.configurator',
        string='Wizard',
    )
    # TODO: Current value ids to save frontend/backend session?
