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
