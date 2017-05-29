# -*- coding: utf-8 -*-

from lxml import etree

from openerp.osv import orm
from openerp import api, models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    subattr_prefix = '__subproduct_attribute-'

    @api.multi
    def onchange(self, values, field_name, field_onchange):
        fld_type = type(field_name)
        if fld_type == list or not field_name.startswith(self.subattr_prefix):
            res = super(ProductConfigurator, self).onchange(
                values, field_name, field_onchange)
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

        available_variants = self.env['product.product'].search([
            ('product_tmpl_id', '=', subproduct.id),
            ('attribute_value_ids', 'in', value_ids)
        ])

        domain = []

        subattr_fields = [
            k for k, v in values.iteritems() if k.startswith(self.subattr_prefix)
        ]

        for k in values:
            attr_id = int(k.split(self.field_prefix)[1])

        attr_vals_map = {
            v.attribute_id.id: v for v in available_variants.mapped('attribute_value_ids')}


        import pdb;pdb.set_trace()

        return res

    @api.model
    def get_subproduct_fields(self, wiz, subproduct, default_attrs=None):
        if not default_attrs:
            default_attrs = {}
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
        return res

    @api.model
    def get_cfg_subproduct_fields(self, wiz, subproduct, default_attrs=None):
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
        subproduct = active_step.config_subproduct_line_id.subproduct_id
        default_attrs = self.get_field_default_attrs()

        if subproduct.config_ok:
            config_fields = self.get_config_subproduct_fields(
                wiz, subproduct, default_attrs)
            res.update(config_fields)
        else:
            # If we have a regular subproduct generate fields for searching
            variant_search_fields = self.get_subproduct_fields(
                wiz, subproduct, default_attrs)
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

        # TODO: Change the structure in such a way where no extra calls
        # are needed
        # Recall method to get the new sub-attribute fields
        dynamic_fields = {
            k: v for k, v in fields.iteritems() if k.startswith(
                self.subattr_prefix)
        }
        res['fields'].update(dynamic_fields)
        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        xml_view = super(ProductConfigurator, self).add_dynamic_fields(
            res=res, dynamic_fields=dynamic_fields, wiz=wiz)

        active_step = wiz.get_active_step()

        # Continue only if current step has a subproduct defined
        subproduct = active_step.config_subproduct_line_id.subproduct_id

        if not subproduct:
            return xml_view

        # TODO: Find a better method for both instances of this method
        # to have all the fields passed beforehand

        dynamic_form = xml_view.xpath("//group[@name='dynamic_form']")[0]
        subproduct_group = etree.Element(
            'group',
            name='subproduct_group',
            string=subproduct.name,
            colspan='3',
        )
        dynamic_form.getparent().insert(0, subproduct_group)
        fields = self.fields_get()

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
                subproduct_group.append(node)
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
