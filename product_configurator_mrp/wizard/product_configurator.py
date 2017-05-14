# -*- coding: utf-8 -*-

from lxml import etree

from openerp.osv import orm
from openerp import api, models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    subattr_prefix = '__subproduct_attribute-'

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
            # TODO: Move logic to separate method
            subproduct_attr_lines = subproduct.mapped('attribute_line_ids')
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
        else:
            # TODO: Move logic to separate method
            # Insert subconfigurable product logic here
            substeps = wiz.config_session_id.get_substeps()

            for step in substeps:
                res['__substep_%d' % step.id] = dict(
                    default_attrs,
                    type='selection',
                    string=step.config_step_id.name,
                )
        # If we have a regular subproduct generate fields for searching
        return res

        # attr_fields = any(f.startswith(self.field_prefix) for f in res)
        # custom_fields = any(
        #     f.startswith(self.custom_field_prefix) for f in res)
        # # If we do not have any dynamic fields to not inject
        # if not attr_fields and not custom_fields:
        #     return res

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

        wiz = self.browse(wizard_id)

        fields = self.fields_get()
        # Recall method to get the new sub-attribute fields
        dynamic_fields = {
            k: v for k, v in fields.iteritems() if k.startswith(
                self.subattr_prefix)
        }
        import pdb;pdb.set_trace()
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

        xml_dynamic_form = xml_view.xpath("//group[@name='dynamic_form']")[0]

        fields = self.fields_get()

        if subproduct.config_ok:
            pass
            # TODO: Implement functionality for subconfigurable products here
        else:
            attrs = {
                'readonly': ['|'],
                'required': [],
                'invisible': ['|']
            }
            attr_lines = subproduct.attribute_line_ids
            for attr_line in attr_lines:
                attribute_id = attr_line.attribute_id.id
                field_name = self.subattr_prefix + str(attribute_id)

                # Check if the attribute line has been added to the db fields
                import pdb;pdb.set_trace()
                if field_name not in fields:
                    continue

                onchange_str = "onchange_attribute_value(%s, context)"
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
                xml_dynamic_form.append(node)
        import pdb;pdb.set_trace()
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
