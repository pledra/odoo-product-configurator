# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ConfigurationRules(TransactionCase):

    def setUp(self):
        super(ConfigurationRules, self).setUp()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')
        self.attr_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.so = self.env.ref('sale.sale_order_5')

    def get_attr_values(self, attr_val_ext_ids=None):
        if not attr_val_ext_ids:
            attr_val_ext_ids = []
        ext_id_prefix = 'product_configurator.product_attribute_value_%s'
        attr_vals = self.env['product.attribute.value']

        for ext_id in attr_val_ext_ids:
            attr_vals += self.env.ref(ext_id_prefix % ext_id)

        return attr_vals

    def get_wizard_write_dict(self, wizard, attr_values):
        """Turn a series of attribute.value objects to a dictionary meant for
        writing values to the product.configurator wizard"""

        write_dict = {}

        multi_attr_ids = wizard.product_tmpl_id.attribute_line_ids.filtered(
            lambda x: x.multi).mapped('attribute_id').ids

        for val in attr_values:
            field_name = wizard.field_prefix + str(val.attribute_id.id)
            if val.attribute_id.id in multi_attr_ids:
                write_dict.setdefault(field_name, [(6, 0, [])])
                write_dict[field_name][0][2].append(val.id)
                continue
            write_dict.update({field_name: val.id})

        return write_dict

    def wizard_write_proceed(self, wizard, attr_vals, value_ids=None):
        """Writes config data to the wizard then proceeds to the next step"""
        vals = self.get_wizard_write_dict(wizard, attr_vals)
        wizard.write(vals)
        wizard.action_next_step()
        # Store the values since the wizard removes dynamic values from dict
        if type(value_ids) == list:
            value_ids += attr_vals.ids

    def test_wizard_configuration(self):
        """Test product configurator wizard"""

        # Start a new configuration wizard
        wizard_obj = self.env['product.configurator'].with_context({
            'active_model': 'sale.order',
            'active_id': self.so.id
        })

        wizard = wizard_obj.create({'product_tmpl_id': self.cfg_tmpl.id})
        wizard.action_next_step()

        value_ids = []

        attr_vals = self.get_attr_values(['gasoline', '228i'])
        self.wizard_write_proceed(wizard, attr_vals, value_ids)

        attr_vals = self.get_attr_values(['silver', 'rims_387'])
        self.wizard_write_proceed(wizard, attr_vals, value_ids)

        attr_vals = self.get_attr_values(['model_sport_line'])
        self.wizard_write_proceed(wizard, attr_vals, value_ids)

        attr_vals = self.get_attr_values(['tapistry_black'])
        self.wizard_write_proceed(wizard, attr_vals, value_ids)

        attr_vals = self.get_attr_values(['steptronic', 'tow_hook', 'sunroof'])
        vals = self.get_wizard_write_dict(wizard, attr_vals)
        wizard.write(vals)
        value_ids += attr_vals.ids

        self.assertTrue(set(wizard.value_ids.ids) == set(value_ids),
                        "Wizard write did not update the config session")

        wizard.action_next_step()

        config_variants = self.env['product.product'].search([
            ('config_ok', '=', True)
        ])

        self.assertTrue(len(config_variants) == 1,
                        "Wizard did not create a configurable variant")

    def test_reconfiguration(self):
        """Test reconfiguration functionality of the wizard"""
        self.test_wizard_configuration()

        order_line = self.so.order_line.filtered(
            lambda l: l.product_id.config_ok
        )

        reconfig_action = order_line.reconfigure_product()

        wizard = self.env['product.configurator'].browse(
            reconfig_action.get('res_id')
        )

        attr_vals = self.get_attr_values(['diesel', '220d'])
        self.wizard_write_proceed(wizard, attr_vals)

        # Cycle through steps until wizard ends
        while wizard.action_next_step():
            pass

        config_variants = self.env['product.product'].search([
            ('config_ok', '=', True)
        ])

        self.assertTrue(len(config_variants) == 2,
                        "Wizard reconfiguration did not create a new variant")

    def test_wizard_domains(self):
        """Test product configurator wizard default values"""

        # Start a new configuration wizard
        wizard = self.env['product.configurator'].create({
            'product_tmpl_id': self.cfg_tmpl.id
        })

        dynamic_fields = {}
        for attribute_line in self.cfg_tmpl.attribute_line_ids:
            field_name = '%s%s' % (
                wizard.field_prefix,
                attribute_line.attribute_id.id
            )
            dynamic_fields[field_name] = [] if attribute_line.multi else False

        attr_gasoline_vals = self.get_attr_values(['gasoline'])
        attr_gasoline_dict = self.get_wizard_write_dict(wizard,
                                                        attr_gasoline_vals)
        attr_218i_vals = self.get_attr_values(['218i'])
        attr_218i_dict = self.get_wizard_write_dict(wizard, attr_218i_vals)
        gasoline_engine_vals = self.env.ref(
            'product_configurator.product_config_line_gasoline_engines'
        ).value_ids

        oc_vals = dynamic_fields.copy()
        oc_vals.update({'id': wizard.id,
                        })
        oc_vals.update(attr_gasoline_dict)
        oc_result = wizard.onchange(
            oc_vals,
            attr_gasoline_dict.keys()[0],
            {}
        )
        k, v = attr_218i_dict.iteritems().next()
        self.assertEqual(
            oc_result.get('value', {}).get(k),
            v,
            "Engine default value not set correctly by onchange wizard"
        )
        oc_domain = oc_result.get('domain', {}).get(k, [])
        domain_ids = oc_domain and oc_domain[0][2] or []
        self.assertEqual(
            set(domain_ids),
            set(gasoline_engine_vals.ids),
            "Engine domain value not set correctly by onchange wizard"
        )
