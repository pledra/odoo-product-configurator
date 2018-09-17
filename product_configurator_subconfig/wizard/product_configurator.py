from lxml import etree

from openerp.osv import orm
from openerp import api, models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    @property
    def _prefixes(self):
        """Add extra field prefixes to the configurator for subproducts"""
        res = super(ProductConfigurator, self)._prefixes
        res.update({
            'subattr_prefix': '__subproduct_attribute-',
        })
        return res

    @api.multi
    def get_state_selection(self):
        """Remove select template step for subconfigurable products"""
        res = super(ProductConfigurator, self).get_state_selection()
        if self._context.get('subproduct_config'):
            res.pop(0)
        return res

    @api.multi
    def onchange(self, values, field_name, field_onchange):

        subattr_prefix = self._prefixes.get('subattr_prefix')

        res = super(ProductConfigurator, self).onchange(
            values=values, field_name=field_name,
            field_onchange=field_onchange
        )

        fld_type = type(field_name)
        if fld_type == list or not field_name.startswith(subattr_prefix):
            return res

        active_step = self.config_session_id.get_active_step()
        subproduct = active_step.config_subproduct_line_id.subproduct_id

        if not subproduct:
            # Raise warning ?
            return res

        subattr_vals = {
            k: values[k] for k in values if k.startswith(subattr_prefix)
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
            field_name = subattr_prefix + str(val.attribute_id.id)
            if field_name not in values:
                continue
            if field_name not in res['domain']:
                res['domain'][field_name] = [('id', 'in', [val.id])]
            else:
                res['domain'][field_name][0][2].append(val.id)

        return res

    @api.model
    def get_subproduct_fields(self, wiz, subproduct_line, default_attrs=None):
        subattr_prefix = self._prefixes.get('subattr_prefix')
        if not default_attrs:
            default_attrs = {}
        subproduct = subproduct_line.subproduct_id
        subproduct_attr_lines = subproduct.mapped('attribute_line_ids')
        res = {}
        for line in subproduct_attr_lines:
            attribute = line.attribute_id
            value_ids = line.value_ids.ids
            res[subattr_prefix + str(attribute.id)] = dict(
                default_attrs,
                type='many2one',
                domain=[('id', 'in', value_ids)],
                string=line.attribute_id.name,
                relation='product.attribute.value',
                sequence=line.sequence,
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

        active_step = wiz.config_session_id.get_active_step()
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
        subattr_prefix = self._prefixes.get('subattr_prefix')

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
            k: v for k, v in fields.items() if k.startswith(subattr_prefix)
        }
        res['fields'].update(dynamic_fields)
        # Send child_ids field to view
        res['fields'].update(child_ids=subsessions_field)
        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        subattr_prefix = self._prefixes.get('subattr_prefix')
        xml_view = super(ProductConfigurator, self).add_dynamic_fields(
            res=res, dynamic_fields=dynamic_fields, wiz=wiz)

        active_step = wiz.config_session_id.get_active_step()

        cfg_steps = wiz.product_tmpl_id.config_step_line_ids
        # Continue only if product.template has substeps defined
        subproducts = any(step.config_subproduct_line_id for step in cfg_steps)

        # TODO: Find a better method for both instances of this method
        # to have all the fields passed beforehand
        fields = self.fields_get()
        dynamic_form = xml_view.xpath("//group[@name='dynamic_form']")[0]

        if not subproducts and not wiz.child_ids or not active_step:
            return xml_view

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
                field_name = subattr_prefix + str(attribute_id)

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

        return xml_view

    @api.multi
    def action_previous_step(self):
        """When a subproduct is loaded switch wizard to new config session"""
        res = super(ProductConfigurator, self).action_previous_step()
        active_step = self.config_session_id.get_active_step()
        adjacent_steps = self.config_session_id.get_adjacent_steps(
            active_step_line_id=active_step.id
        )
        prev_step = adjacent_steps.get('prev_step')
        parent_session = self.config_session_id.parent_id

        if not active_step and prev_step and parent_session:
            self.write({
                'product_tmpl_id': prev_step.product_tmpl_id.id,
                'config_session_id': parent_session.id,
                'state': str(prev_step.id),
            })
        return res

    @api.multi
    def action_next_step(self):
        """Override parent method to support subconfiguration navigation"""
        res = super(ProductConfigurator, self).action_next_step()
        # Here the state has been changed and we are already on the next step
        # TODO: Find a better way to detect if wizard has been set to done
        if not res or not self.exists():
            return res

        cfg_session_obj = self.env['product.config.session']
        cfg_step_line_obj = self.env['product.config.step.line']

        # Active step is set on the wizard so we browse that instead of session
        active_step = self.env['product.config.step.line'].browse(
            int(self.state)
        )
        parent_product_tmpl = self.parent_id.product_tmpl_id

        subproduct_line = active_step.config_subproduct_line_id
        subproduct = subproduct_line.subproduct_id.sudo()

        # If the active step belongs to another template we should point the
        # wizard towards the parent session to reflect the active configuration
        # This happens at the end of a subconfiguration process only
        if active_step.product_tmpl_id != self.product_tmpl_id:
            valid_conf = self.config_session_id.validate_configuration()
            if not valid_conf:
                open_steps = self.config_session_id.get_open_step_lines(
                    value_ids=self.value_ids.ids
                )
                self.state = open_steps[0].id
                return res

            # If configuration is valid set session to done and navigate up
            self.config_session_id.action_confirm()
            self.write({
                'config_session_id': self.parent_id.id,
                'product_tmpl_id': parent_product_tmpl.id,
            })
            return res

        if not subproduct or not subproduct.config_ok:
            return res

        # Get all current subsessions for this subproduct
        sessions = self.child_ids.filtered(
            lambda s: s.product_tmpl_id == subproduct)

        # If there is no subsession defined but it is required create one
        # TODO: and subproduct_line.required and add cfg new subproduct button
        if not sessions:
            sessions = cfg_session_obj.create_get_session(
                subproduct.id, parent_id=self.config_session_id.id)

        draft_sessions = sessions.filtered(lambda s: s.state == 'draft')

        # If this session does not have any draft subsessions skip
        if not draft_sessions:
            return res

        session = draft_sessions[0]
        session_step = cfg_session_obj
        # If the session has a saved step write it on the wizard
        # TODO: Move to separate method
        if session.config_step:
            try:
                step_id = int(session.config_step)
                session_step = cfg_step_line_obj.browse(step_id)
            except Exception:
                pass
        if not session_step:
            open_steps = session.get_open_step_lines(session.value_ids.ids)
            if open_steps:
                session_step = open_steps[0]

        # TODO: Go to last subproduct in draft state not step just before

        self.write({
            'config_session_id': session.id,
            'product_tmpl_id': subproduct.id,
            'state': session_step.id,
            'config_step': session_step.id,
        })

        # If this is a subsession add context flag to remove 'select' step
        if self.parent_id:
            res['context'].update({'subproduct_config': True})

        return res

    @api.multi
    def write(self, vals):
        if not vals:
            vals = {}

        subattr_prefix = self._prefixes.get('subattr_prefix')

        res = super(ProductConfigurator, self).write(vals=vals)

        subproduct_value_ids = [
            v for k, v in vals.items() if k.startswith(subattr_prefix)
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

        product_vals = {
            'user_id': self.env.uid,
            'parent_id': self.config_session_id.id,
            'value_ids': [(6, 0, subproduct[0].attribute_value_ids.ids)],
            'state': 'done',
            'product_tmpl_id': product_tmpl_id,
        }

        self.env['product.config.session'].create(product_vals)
        return res
