# -*- coding: utf-8 -*-

from lxml import etree

from openerp.osv import orm
from openerp import api, models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    subattr_prefix = '__subproduct_attribute-'
    subattr_qty_prefix = '__subproduct_qty-'

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        res = super(ProductConfigurator, self).onchange(
            values=values, field_name=field_name,
            field_onchange=field_onchange
        )

        fld_type = type(field_name)
        if fld_type == list or not field_name.startswith(self.subattr_prefix):
            return res

        # Maybe we store the subproduct instead of searching for it?
        active_step = self.get_active_step()
        subproduct = active_step.config_subproduct_line_id.subproduct_id

        if not subproduct:
            # Raise warning ?
            return res

        subattr_vals = {
            k: values[k] for k in values if k.startswith(self.subattr_prefix)
        }

        value_ids = [attr_id for attr_id in subattr_vals.values() if attr_id]

        domain = [('product_tmpl_id', '=', subproduct.id)]
        domain += [
            ('attribute_value_ids', '=', val_id) for val_id in value_ids
        ]

        available_variants = self.env['product.product'].search(domain)
        available_attr_vals = available_variants.mapped('attribute_value_ids')

        res['domain'] = res.get('domain', {})
        res['value'] = res.get('value', {})

        # Build domain to restrict options to existing variants only
        for val in available_attr_vals:
            field_name = self.subattr_prefix + str(val.attribute_id.id)
            if field_name not in values:
                continue
            if field_name not in res['domain']:
                res['domain'][field_name] = [('id', 'in', [val.id])]
            else:
                res['domain'][field_name][0][2].append(val.id)

        return res

    @api.model
    def get_subproduct_fields(self, wiz, subproduct_line, default_attrs=None):
        if not default_attrs:
            default_attrs = {}
        subproduct = subproduct_line.subproduct_id
        subproduct_attr_lines = subproduct.mapped('attribute_line_ids')
        res = {}
        for line in subproduct_attr_lines:
            attribute = line.attribute_id
            value_ids = line.value_ids.ids
            res[self.subattr_prefix + str(attribute.id)] = dict(
                default_attrs,
                type='many2one',
                domain=[('id', 'in', value_ids)],
                string=line.attribute_id.name,
                relation='product.attribute.value',
                sequence=line.sequence,
            )
        if subproduct_line.quantity:
            res[self.subattr_qty_prefix + str(subproduct.id)] = dict(
                default_attrs,
                type='integer',
                default='1',
                string='Quantity'
            )
        return res

    @api.model
    def get_cfg_subproduct_fields(
            self, wiz, subproduct_line, default_attrs=None):
        if not default_attrs:
            default_attrs = {}
        substeps = wiz.config_session_id.get_substeps()
        res = {}

        for step in substeps:
            res['__substep_%d' % step.id] = dict(
                default_attrs,
                type='selection',
                string=step.config_step_id.name,
            )
        return res

    # Add state fields for all subproducts to dynamic field list
    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        res = super(ProductConfigurator, self).fields_get(
            allfields=allfields, write_access=write_access,
            attributes=attributes
        )

        wizard_id = self.env.context.get('wizard_id')

        if not wizard_id:
            return res

        wiz = self.browse(wizard_id)

        # If the product template is not set it is still at the 1st step
        product_tmpl = wiz.product_tmpl_id
        if not product_tmpl:
            return res

        active_step = wiz.get_active_step()
        subproduct_line = active_step.config_subproduct_line_id
        default_attrs = self.get_field_default_attrs()

        if not subproduct_line.subproduct_id.config_ok:
            # If we have a regular subproduct generate fields for searching
            variant_search_fields = self.get_subproduct_fields(
                wiz, subproduct_line, default_attrs)
            res.update(variant_search_fields)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):

        res = super(ProductConfigurator, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu
        )
        wizard_id = self.env.context.get('wizard_id')

        if res.get('type') != 'form' or not wizard_id:
            return res

        fields = self.fields_get()
        subsessions_field = fields.get('child_ids')
        subsessions_field.update(views={})

        # TODO: Change the structure in such a way where no extra calls
        # are needed
        # Recall method to get the new sub-attribute fields
        dynamic_fields = {
            k: v for k, v in fields.iteritems() if k.startswith(
                self.subattr_prefix) or k.startswith(self.subattr_qty_prefix)
        }
        res['fields'].update(dynamic_fields)
        # Send child_ids field to view
        res['fields'].update(child_ids=subsessions_field)
        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        xml_view = super(ProductConfigurator, self).add_dynamic_fields(
            res=res, dynamic_fields=dynamic_fields, wiz=wiz)

        active_step = wiz.get_active_step()

        cfg_steps = wiz.product_tmpl_id.config_step_line_ids
        # Continue only if product.template has substeps defined
        subproducts = any(step.config_subproduct_line_id for step in cfg_steps)

        if not subproducts or not active_step:
            return xml_view

        # TODO: Find a better method for both instances of this method
        # to have all the fields passed beforehand
        fields = self.fields_get()
        dynamic_form = xml_view.xpath("//group[@name='dynamic_form']")[0]

        subproduct_notebook = etree.Element(
            'notebook',
            colspan='4',
            name='subproduct_notebook',
        )
        dynamic_form.getparent().insert(0, subproduct_notebook)

        # Get the active subproduct
        subproduct_line = active_step.config_subproduct_line_id
        subproduct = subproduct_line.subproduct_id
        cfg_subproducts = wiz.child_ids.mapped('product_tmpl_id')

        active_subproduct = (subproduct and subproduct
                             not in cfg_subproducts or subproduct_line.multi)

        if active_subproduct:
            subproduct_config_page = etree.Element(
                'page',
                name='subproduct_form',
                string='Subproduct Configuration',
            )
            subproduct_config_group = etree.Element(
                'group',
                name='subproduct_config_group',
            )
            subproduct_config_page.append(subproduct_config_group)
            subproduct_notebook.append(subproduct_config_page)

        subproducts_page = etree.Element(
            'page',
            name='subproducts',
            string='Subproducts',
        )
        subproduct_notebook.append(subproducts_page)

        subproduct_group = etree.Element(
            'group',
            name='subproduct_group',
        )
        subproducts_page.append(subproduct_group)

        subsessions_field = etree.Element(
            'field',
            name='child_ids',
            widget='one2many',
            context=str({
                'tree_view_ref': '%s.%s' % (
                    'product_configurator_mrp',
                    'product_config_session_subproducts_tree_view'
                )
            }),
            colspan='4',
            nolabel='1',
        )
        orm.setup_modifiers(subsessions_field)
        subproduct_group.append(subsessions_field)

        if not active_subproduct:
            return xml_view

        if subproduct.config_ok:
            pass
            # TODO: Implement functionality for subconfigurable products here
        else:
            attr_lines = subproduct.attribute_line_ids
            if not attr_lines:
                # Go to checkout as we have only one variant
                return xml_view
            attrs = {
                'readonly': ['|'],
                'required': [],
                'invisible': ['|']
            }
            for attr_line in attr_lines:
                attribute_id = attr_line.attribute_id.id
                field_name = self.subattr_prefix + str(attribute_id)

                # Check if the attribute line has been added to the db fields
                if field_name not in fields:
                    continue

                onchange_str = "onchange_subattr_value(%s, context)"
                node = etree.Element(
                    "field",
                    name=field_name,
                    on_change=onchange_str % field_name,
                    required='True' if subproduct_line.required else '',
                    default_focus="1" if attr_line == attr_lines[0] else "0",
                    attrs=str(attrs),
                    context="{'show_attribute': False}",
                    options=str({
                        'no_create': True,
                        'no_create_edit': True,
                        'no_open': True
                    })
                )
                orm.setup_modifiers(node)
                subproduct_config_group.append(node)

            qty_field = self.subattr_qty_prefix + str(subproduct.id)
            if qty_field in fields:
                node = etree.Element(
                    "field",
                    name=qty_field,
                    on_change=onchange_str % field_name,
                    required='True'
                )
                orm.setup_modifiers(node)
                subproduct_config_group.append(node)

        return xml_view

    @api.multi
    def action_next_step(self):
        """When a subproduct is loaded switch wizard to new config session"""
        res = super(ProductConfigurator, self).action_next_step()
        active_step = self.get_active_step()
        if active_step and active_step.product_tmpl_id != self.product_tmpl_id:
            session = self.env['product.config.session'].create_get_session(
                product_tmpl_id=active_step.product_tmpl_id.id,
                parent_id=self.config_session_id.id
            )
            self.write({
                'product_tmpl_id': active_step.product_tmpl_id.id,
                'config_session_id': session.id
            })
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductConfigurator, self).write(vals=vals)

        subproduct_value_ids = [
            v for k, v in vals.iteritems() if k.startswith(self.subattr_prefix)
        ]

        if not subproduct_value_ids:
            return res

        subproduct = self.env['product.product'].search([
            ('attribute_value_ids', '=', vid) for vid in subproduct_value_ids
        ])

        if not subproduct:
            # TODO: Raise error?
            return res

        product_tmpl_id = subproduct[0].product_tmpl_id.id
        qty_field = self.subattr_qty_prefix + str(product_tmpl_id)

        product_vals = {
            'user_id': self.env.uid,
            'parent_id': self.config_session_id.id,
            'value_ids': [(6, 0, subproduct[0].attribute_value_ids.ids)],
            'product_tmpl_id': product_tmpl_id,
            'quantity': vals.get(qty_field, 1),
        }

        self.env['product.config.session'].create(product_vals)
        return res
