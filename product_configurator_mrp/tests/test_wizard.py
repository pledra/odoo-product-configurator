from odoo.tests.common import TransactionCase
from odoo import SUPERUSER_ID


class Wizard(TransactionCase):

    def setUp(self):
        super(Wizard, self).setUp()

        self.cfg_tmpl = self.env.ref('product_configurator.bmw_2_series')
        self.cfg_wizard = self.env['product.configurator'].create({
            'product_tmpl_id': self.cfg_tmpl.id,
            'user_id': SUPERUSER_ID
        })

        self.cfg_session = self.cfg_wizard.config_session_id

        attribute_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')
        self.attr_vals = self.cfg_tmpl.attribute_line_ids.mapped('value_ids')

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

    def test_wizard_configuration(self):
        """Test whether the configuration lines and quantities and being created
        and maintained properly by the wizard"""

        conf = [
            'gasoline', '228i', 'model_luxury_line', 'silver', 'rims_384',
            'tapistry_black', 'steptronic', 'smoker_package', 'tow_hook'
        ]

        attr_val_ids = set(self.get_attr_val_ids(conf))

        field_prefix = self.cfg_wizard._prefixes['field_prefix']
        qty_field_prefix = self.cfg_wizard._prefixes['attr_val_product_qty']
        # Proceed to the first configuration step after selecting template

        attr_product_count = 0

        while self.cfg_wizard:
            state = self.cfg_wizard.state
            self.cfg_wizard.action_next_step()

            if self.cfg_wizard.state == state:
                break

            step_id = int(self.cfg_wizard.state)

            cfg_step = self.cfg_tmpl.config_step_line_ids.filtered(
                lambda cfg_step: cfg_step.id == step_id
            )

            attr_lines = cfg_step.mapped('attribute_line_ids')

            vals = {}

            for attr_line in attr_lines:
                attr_vals = attr_line.value_ids.filtered(
                    lambda attr_val: attr_val.id in attr_val_ids
                )
                for attr_val in attr_vals:
                    if attr_val.product_id and not attr_line.multi:
                        attr_product_count += 1
                    attribute_id = attr_val.attribute_id.id
                    field_name = field_prefix + str(attribute_id)
                    qty_field_name = qty_field_prefix + str(attribute_id)
                    if attr_line.multi:
                        if field_name not in vals:
                            vals[field_name] = [(0, 0, [])]
                        vals[field_name][0][2].append(attr_val.id)
                    else:
                        vals.update({
                            field_name: attr_val.id,
                            qty_field_name: 1
                        })

            self.cfg_wizard.write(vals)

        cfg_bom_line_ids = self.cfg_session.cfg_bom_line_ids

        self.assertTrue(
            len(cfg_bom_line_ids) == attr_product_count,
            "Number of cfg_lines on the configuration session do not match "
            "the number of related products set on the attributes of the "
            "given configuration"
        )
