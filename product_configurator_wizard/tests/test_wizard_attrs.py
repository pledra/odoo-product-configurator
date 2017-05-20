# -*- coding: utf-8 -*-

from odoo.addons.product_configurator_wizard.tests.test_wizard \
    import ConfigurationRules


class ConfigurationAttributes(ConfigurationRules):

    def setUp(self):
        """
        Product with 3 sizes:
            Small or Medium allow Blue or Red, but colour is optional
            Large does not allow colour selection
        """
        super(ConfigurationAttributes, self).setUp()

        self.attr_size = self.env['product.attribute'].create(
            {'name': 'Size'})
        self.attr_val_small = self.env['product.attribute.value'].create(
            {'attribute_id': self.attr_size.id,
             'name': 'Small',
             }
        )
        self.attr_val_med = self.env['product.attribute.value'].create(
            {'attribute_id': self.attr_size.id,
             'name': 'Medium',
             }
        )
        self.attr_val_large = self.env['product.attribute.value'].create(
            {'attribute_id': self.attr_size.id,
             'name': 'Large (Green)',
             }
        )
        domain_small_med = self.env['product.config.domain'].create(
            {'name': 'Small/Med',
             'domain_line_ids': [
                 (0, 0, {'attribute_id': self.attr_size.id,
                         'condition': 'in',
                         'operator': 'and',
                         'value_ids':
                             [(6, 0,
                               [self.attr_val_small.id, self.attr_val_med.id]
                               )]
                         }),
                 ],
             }
        )
        self.attr_colour = self.env['product.attribute'].create(
            {'name': 'Colour'})
        self.attr_val_blue = self.env['product.attribute.value'].create(
            {'attribute_id': self.attr_colour.id,
             'name': 'Blue',
             }
        )
        self.attr_val_red = self.env['product.attribute.value'].create(
            {'attribute_id': self.attr_colour.id,
             'name': 'Red',
             }
        )
        self.product_temp = self.env['product.template'].create(
            {'name': 'Config Product',
             'config_ok': True,
             'type': 'product',
             'categ_id': self.env['ir.model.data'].xmlid_to_res_id(
                 'product.product_category_5'
             ),
             'attribute_line_ids': [
                 (0, 0, {'attribute_id': self.attr_size.id,
                         'value_ids': [
                             (6, 0, self.attr_size.value_ids.ids),
                             ],
                         'required': True,
                         }),
                 (0, 0, {'attribute_id': self.attr_colour.id,
                         'value_ids': [
                             (6, 0, self.attr_colour.value_ids.ids),
                             ],
                         'required': False,
                         })
                 ],
             }
        )
        colour_line = self.product_temp.attribute_line_ids.filtered(
            lambda a: a.attribute_id == self.attr_colour)
        self.env['product.config.line'].create({
            'product_tmpl_id': self.product_temp.id,
            'attribute_line_id': colour_line.id,
            'value_ids': [(6, 0, self.attr_colour.value_ids.ids)],
            'domain_id': domain_small_med.id,
            })

    def test_configurations_option_or_not_reqd(self):
        # Start a new configuration wizard
        wizard_obj = self.env['product.configurator'].with_context({
            'active_model': 'sale.order',
            'active_id': self.so.id
            # 'default_order_id': self.so.id
        })

        wizard = wizard_obj.create({'product_tmpl_id': self.product_temp.id})
        wizard.action_next_step()

        dynamic_fields = {}
        for attribute_line in self.product_temp.attribute_line_ids:
            field_name = '%s%s' % (
                wizard.field_prefix,
                attribute_line.attribute_id.id
            )
            dynamic_fields[field_name] = [] if attribute_line.multi else False
        field_name_colour = '%s%s' % (
            wizard.field_prefix,
            self.attr_colour.id
        )
        invisible_name_colour = '%s%s' % (
            wizard.invisible_field_prefix,
            self.attr_colour.id
        )
        invisible_name_size = '%s%s' % (
            wizard.invisible_field_prefix,
            self.attr_size.id
        )

        # Define small without colour specified
        self.wizard_write_proceed(wizard, [self.attr_val_small])
        new_variant = self.product_temp.product_variant_ids
        self.assertTrue(len(new_variant) == 1 and
                        set(new_variant.attribute_value_ids.ids) ==
                        set([self.attr_val_small.id]),
                        "Wizard did not accurately create a variant with "
                        "optional value undefined")
        config_variants = self.product_temp.product_variant_ids

        order_line = self.so.order_line.filtered(
            lambda l: l.product_id.config_ok
        )

        # Redefine to medium without colour
        self.do_reconfigure(order_line, [self.attr_val_med])
        new_variant = self.product_temp.product_variant_ids - config_variants
        self.assertTrue(len(new_variant) == 1 and
                        set(new_variant.attribute_value_ids.ids) ==
                        set([self.attr_val_med.id]),
                        "Wizard did not accurately reconfigure a variant with "
                        "optional value undefined")
        config_variants = self.product_temp.product_variant_ids

        # Redefine to medium blue
        self.do_reconfigure(order_line, [self.attr_val_blue])
        new_variant = self.product_temp.product_variant_ids - config_variants
        self.assertTrue(len(new_variant) == 1 and
                        set(new_variant.attribute_value_ids.ids) ==
                        set([self.attr_val_med.id, self.attr_val_blue.id]),
                        "Wizard did not accurately reconfigure a variant with "
                        "to add an optional value")
        config_variants = self.product_temp.product_variant_ids

        # Redefine to large - should remove colour, as this is invalid
        reconfig_action = order_line.reconfigure_product()
        wizard = self.env['product.configurator'].browse(
            reconfig_action.get('res_id')
        )
        attr_large_dict = self.get_wizard_write_dict(wizard,
                                                     [self.attr_val_large])
        attr_blue_dict = self.get_wizard_write_dict(wizard,
                                                    [self.attr_val_blue])
        oc_vals = dynamic_fields.copy()
        oc_vals.update({'id': wizard.id})
        oc_vals.update(dict(attr_blue_dict, **attr_large_dict))
        oc_result = wizard.onchange(
            oc_vals,
            attr_large_dict.keys()[0],
            {}
        )
        self.assertTrue(field_name_colour in oc_result['value'] and
                        not oc_result['value'][field_name_colour],
                        "Colour should have been cleared by wizard"
                        )
        self.assertTrue(invisible_name_colour in oc_result['value'] and
                        not oc_result['value'][invisible_name_colour],
                        "Invisible Attribute Colour should have been "
                        "cleared by wizard"
                        )
        self.assertTrue(invisible_name_size in oc_result['value'] and
                        oc_result['value'][invisible_name_size] ==
                        self.attr_val_large.id,
                        "Invisible Attribute Size should have been set "
                        "by wizard"
                        )
        vals = self.get_wizard_write_dict(wizard, [self.attr_val_large],
                                          remove_values=[self.attr_val_blue])
        wizard.write(vals)
        wizard.action_next_step()
        if wizard.exists():
            while wizard.action_next_step():
                pass
        new_variant = self.product_temp.product_variant_ids - config_variants
        self.assertTrue(len(new_variant) == 1 and
                        set(new_variant.attribute_value_ids.ids) ==
                        set([self.attr_val_large.id]),
                        "Wizard did not accurately reconfigure a variant with "
                        "to remove invalid attribute")
