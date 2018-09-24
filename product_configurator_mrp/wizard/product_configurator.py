from lxml import etree

from openerp.osv import orm
from openerp import api, models


class ProductConfigurator(models.TransientModel):
    _inherit = 'product.configurator'

    @property
    def _prefixes(self):
        """Add extra field prefixes to the configurator for quantities"""
        res = super(ProductConfigurator, self)._prefixes
        res.update({
            'attr_val_product_qty': '__attribute_qty-',
        })
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductConfigurator, self).write(vals)

        field_prefix = self._prefixes.get('field_prefix')
        attr_qty_prefix = self._prefixes.get('attr_val_product_qty')

        attr_fields = [f for f in vals if f.startswith(field_prefix)]
        qty_fields = [f for f in vals if f.startswith(attr_qty_prefix)]

        attr_ids = set()

        try:
            attr_ids |= {int(f.split(field_prefix)[1]) for f in attr_fields}
        except Exception:
            pass

        try:
            attr_ids |= {int(f.split(attr_qty_prefix)[1]) for f in qty_fields}
        except Exception:
            pass

        # Do not consider multi selection yet
        attr_lines = self.product_tmpl_id.attribute_line_ids.filtered(
            lambda x: not x.multi and x.attribute_id.id in attr_ids
        )

        for line in attr_lines:

            attribute = line.attribute_id

            attr_field = field_prefix + str(attribute.id)
            qty_field = attr_qty_prefix + str(attribute.id)

            # Obtained entered quantity in the wizard or the default value
            quantity = vals.get(qty_field, 1)

            if not isinstance(quantity, int):
                continue

            if quantity <= 0:
                quantity = 1

            attr_val_id = vals.get(attr_field)

            if attr_val_id:
                try:
                    attr_val_id = int(vals[attr_field])
                    attr_val = self.env['product.attribute.value'].browse(
                        attr_val_id
                    )
                except Exception:
                    continue
            else:
                attr_val = self.config_session_id.value_ids.filtered(
                    lambda attr_val: attr_val.attribute_id == attribute
                )

            if not attr_val.product_id:
                continue

            # Attempt to locate another config line with the same attribute
            cfg_session_line = self.config_session_id.cfg_line_ids.filtered(
                lambda l: l.attr_val_id.attribute_id.id == attribute.id
            )

            # If there are two or more delete all records and set line to None
            if len(cfg_session_line) > 1:
                cfg_session_line.unlink()
                cfg_session_line = None

            # If none exists create one
            if not cfg_session_line:
                line_vals = {
                    'attr_val_id': attr_val.id,
                    'quantity': quantity,
                }
                self.config_session_id.write({
                    'cfg_line_ids': [(0, 0, line_vals)]
                })
            # Else update existing line with current values
            else:
                cfg_session_line.write({
                    'quantity': quantity,
                    'attr_val_id': attr_val.id
                })

        return res

    @api.model
    def get_qty_fields(self):
        """Add quantity fields for attributes that have at least an attribute
        value with quantity selection enabled"""
        wizard_id = self.env.context.get('wizard_id')

        if not wizard_id:
            return {}

        wiz = self.browse(wizard_id)

        if not wiz.product_tmpl_id:
            return {}

        res = {}
        attr_qty_prefix = self._prefixes.get('attr_val_product_qty')
        attr_vals = wiz.product_tmpl_id.attribute_line_ids.filtered(
            lambda l: not l.multi).mapped('value_ids')
        qty_attr_vals = attr_vals.filtered(
            lambda attr_val: attr_val.product_id and attr_val.quantity
        )

        for attribute in qty_attr_vals.mapped('attribute_id'):
            default_attrs = self.get_field_default_attrs()
            res[attr_qty_prefix + str(attribute.id)] = dict(
                default_attrs,
                default="1",
                type='integer',
                string='Quantity',
            )
        return res

    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        """Inject quantity fields where attribute values allow it"""
        res = super(ProductConfigurator, self).fields_get(
            allfields=allfields, write_access=write_access,
            attributes=attributes
        )

        qty_fields = self.get_qty_fields()
        res.update(qty_fields)
        return res

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        """Add quantity fields to view after each dynamic field"""
        xml_view = super(ProductConfigurator, self).add_dynamic_fields(
            res=res, dynamic_fields=dynamic_fields, wiz=wiz
        )

        attr_qty_prefix = self._prefixes.get('attr_val_product_qty')
        field_prefix = self._prefixes.get('field_prefix')
        qty_fields = [
            f for f in res['fields'] if f.startswith(attr_qty_prefix)
        ]

        for qty_field in qty_fields:
            # If the matching attribute field is found in the view add after
            attr_id = int(qty_field.replace(attr_qty_prefix, ''))
            dynamic_attr_product_qty_name = attr_qty_prefix + str(attr_id)
            dynamic_field_name = field_prefix + str(attr_id)
            dynamic_field = xml_view.xpath(
                "//field[@name='%s']" % dynamic_field_name
            )
            if not dynamic_field:
                continue

            active_step = wiz.config_session_id.get_active_step()

            available_attr_ids = active_step.attribute_line_ids.mapped(
                'attribute_id').ids

            if attr_id not in available_attr_ids:
                continue

            qty_field = etree.Element(
                'field',
                name=dynamic_attr_product_qty_name,
                attrs=str({
                    'invisible': [(dynamic_field_name, '=', False)],
                    'readonly': [(dynamic_field_name, '=', False)],
                })
            )
            orm.setup_modifiers(qty_field)
            dynamic_form = dynamic_field[0].getparent()
            dynamic_form.insert(
                dynamic_form.index(dynamic_field[0]) + 1, qty_field
            )
        return xml_view

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        res = super(ProductConfigurator, self).read(fields=fields, load=load)

        attr_qty_prefix = self._prefixes.get('attr_val_product_qty')

        qty_fields = [f for f in fields if f.startswith(attr_qty_prefix)]

        for field in qty_fields:
            try:
                attr_id = int(field.split(attr_qty_prefix)[1])
            except:
                continue

            qty = 1

            cfg_line = self.config_session_id.cfg_line_ids.filtered(
                lambda l: l.attr_val_id.attribute_id.id == attr_id
            )
            if cfg_line:
                qty = cfg_line[0].quantity

            res[0][field] = qty
        return res
