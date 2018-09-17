from odoo.tests.common import TransactionCase


class ConfigurationWizard(TransactionCase):

    def setUp(self):
        super(ConfigurationWizard, self).setUp()
        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')
        self.attr_vals = attribute_vals

        self.attr_val_ext_ids = {
            v: k for k, v in attribute_vals.get_external_id().items()
        }

    def get_attr_val_ids(self, ext_ids):
        """Return a list of database ids using the external_ids
        passed via ext_ids argument"""

        value_ids = []

        attr_val_prefix = 'product_configurator.product_attribute_value_%s'

        for ext_id in ext_ids:
            if ext_id in self.attr_val_ext_ids:
                value_ids.append(self.attr_val_ext_ids[ext_id])
            elif attr_val_prefix % ext_id in self.attr_val_ext_ids:
                value_ids.append(
                    self.attr_val_ext_ids[attr_val_prefix % ext_id]
                )

        return value_ids

    def create_wizard(self, product_tmpl=None):
        if not product_tmpl:
            product_tmpl = self.cfg_tmpl
        wizard_vals = {
            'product_tmpl_id': product_tmpl.id
        }
        wizard = self.env['product.configurator'].create(vals=wizard_vals)
        return wizard
