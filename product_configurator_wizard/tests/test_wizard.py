# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ConfigurationRules(TransactionCase):

    def setUp(self):
        super(ConfigurationRules, self).setUp()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')
        self.attr_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

        self.so = self.env.ref('sale.sale_order_5')

    def get_wizard_write_dict(self, wizard, attr_val_ext_ids):
        """Turn a series of attribute.value objects to a dictionary meant for
        writing values to the product.configurator wizard"""

        write_dict = {}
        ext_id_prefix = 'product_configurator.product_attribute_value_%s'

        for ext_id in attr_val_ext_ids:
            val = self.env.ref(ext_id_prefix % ext_id)
            write_dict.update({
                wizard.field_prefix + str(val.attribute_id.id): val.id
            })
        return write_dict

    def test_wizard(self):
        """Test product configurator wizard"""

        # Start a new configuration wizard
        wizard = self.env['product.configurator'].create({
            'product_tmpl_id': self.cfg_tmpl.id
        })

        wizard.action_next_step()

        # Get write values the first configuration step
        write_dict = self.get_wizard_write_dict(wizard, ['gasoline', '228i'])

        # Store the values since the wizard removed dynamic values from dict
        write_val_ids = write_dict.values()

        # Test wizard dynamic write
        wizard.write(write_dict)

        self.assertTrue(wizard.value_ids.ids == write_val_ids,
                        "Wizard write did not update the config session")

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

        write_dict_gasoline = self.get_wizard_write_dict(wizard, ['gasoline'])
        write_dict_218i = self.get_wizard_write_dict(wizard, ['218i'])
        gasoline_engine_ids = self.env.ref(
            'product_configurator.product_config_line_gasoline_engines'
        ).value_ids.ids

        oc_vals = dynamic_fields.copy()
        oc_vals.update({'id': wizard.id,
                        })
        oc_vals.update(self.get_wizard_write_dict(wizard, ['gasoline']))
        oc_result = wizard.onchange(
            oc_vals,
            write_dict_gasoline.keys()[0],
            {}
        )
        k, v = write_dict_218i.iteritems().next()
        self.assertEqual(
            oc_result.get('value', {}).get(k),
            v,
            "Engine default value not set correctly by onchange wizard"
        )
        oc_domain = oc_result.get('domain', {}).get(k, [])
        domain_ids = oc_domain and oc_domain[0][2] or []
        self.assertEqual(
            set(domain_ids),
            set(gasoline_engine_ids),
            "Engine domain value not set correctly by onchange wizard"
        )
