# -*- coding: utf-8 -*-

from lxml import etree

from odoo.osv import orm
from odoo import models, api
from odoo.exceptions import Warning


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    # Prefix for the dynamicly injected fields
    mode_prefix = '__mode-'

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """ Inject the mode fields """
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

        # TODO: If last block is attempting to be clever, this next
        # line is ignoring it.  Need to determine what is best.
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
            DISPLAY_SELECTION = [('hide', 'Hide'), ('value', 'Only Value'), ('attribute', 'With Label')]
            res[self.mode_prefix + str(attribute.id)] = dict(
                default_attrs,
                type='selection',
                selection=DISPLAY_SELECTION
            )

        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ override to add mode fields
        """
        # WARNING - super-duper hack to bypass super.fields_view_get()
        # this is a rewrite, parent call cannot be executed
        from odoo.addons.product_configurator_wizard.wizard.product_configurator import ProductConfigurator as SuperProductConfigurator
        res = super(SuperProductConfigurator, self).fields_view_get(
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
            k: v for k, v in fields.iteritems()
                if k.startswith(self.field_prefix)
                or k.startswith(self.custom_field_prefix)
                # CHANGES START
                or k.startswith(self.mode_prefix)
                # CHANGES END
        }

        res['fields'].update(dynamic_fields)
        mod_view = self.add_dynamic_fields(res, dynamic_fields, wiz)

        # Update result dict from super with modified view
        res.update({'arch': etree.tostring(mod_view)})

        # set any default values
        wiz_vals = wiz.read(dynamic_fields.keys())[0]
        dynamic_field_vals = {
            k: wiz_vals.get(
                k, [] if v['type'] == 'many2many' else False
                )
            for k, v in fields.iteritems()
            if k.startswith(self.field_prefix)
        }
        domains = {k: dynamic_fields[k]['domain']
                   for k in dynamic_field_vals.keys()}
        try:
            cfg_step_id = int(wiz.state)
            cfg_step = wiz.product_tmpl_id.config_step_line_ids.filtered(
                lambda x: x.id == cfg_step_id)
        except:
            cfg_step = self.env['product.config.step.line']
        vals = wiz.get_form_vals(dynamic_field_vals, domains, cfg_step)
        if vals:
            wiz.write(vals)
        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        """ override to add mode fields
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

            # CHANGES START
            node = etree.Element(
                'label',
                attrs=str(attrs))
            node.attrib['for'] = field_name  # for is a reserved keyword
            orm.setup_modifiers(node)
            xml_dynamic_form.append(node)
            div = etree.Element('div', style='width: auto;')
            # CHANGES END
            # Create the new field in the view
            node = etree.Element(
                "field",
                # CHANGES START
                style="width: 80%; margin-right: 2%;",
                # CHANGES END
                name=field_name,
                on_change="onchange_attribute_value(%s, context)" % field_name,
                default_focus="1" if attr_line == attr_lines[0] else "0",
                attrs=str(attrs),
                context=str({
                    'show_attribute': False,
                    'product_tmpl_id': wiz.product_tmpl_id.id,
                    'default_attribute_id': attribute_id
                }),
                options=str({
                    'no_create': not attr_line.attribute_id.create_on_fly,
                    'no_create_edit': not attr_line.attribute_id.create_on_fly,
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
            # CHANGES START
            # xml_dynamic_form.append(node)
            div.append(node)
            node = etree.Element(
                'field',
                name=self.mode_prefix + str(attribute_id),
                style="width: auto;",
                attrs=str(attrs),
                readonly="1")
            orm.setup_modifiers(node)
            div.append(node)
            # CHANGES END

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
                # CHANGES START
                # xml_dynamic_form.append(node)
                div.append(node)
            xml_dynamic_form.append(div)
            # CHANGES END

        return xml_view

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Remove mode dynamic fields from the fields list and update the
        returned values with the dynamic data stored in attribute_line_ids"""
        mode_attr_vals = [f for f in fields if f.startswith(self.mode_prefix)]

        dynamic_fields = mode_attr_vals
        fields = [f for f in fields if f not in dynamic_fields]
        dynamic_vals = {}

        res = super(ProductConfigurator, self).read(fields=fields, load=load)

        if not dynamic_fields:
            return res

        for attr_line in self.product_tmpl_id.attribute_line_ids:
            res[0][self.mode_prefix + str(attr_line.attribute_id.id)] = attr_line.display_mode
        return res

    @api.multi
    def write(self, vals):
        """Prevent database storage of mode dynamic fields"""

        # Get current database value_ids (current configuration)

        for attr_line in self.product_tmpl_id.attribute_line_ids:
            # readonly, no need to write them
            mode_field_name = self.mode_prefix + str(attr_line.attribute_id.id)
            if mode_field_name in vals:
                del vals[mode_field_name]

        res = super(ProductConfigurator, self).write(vals)
        return res
