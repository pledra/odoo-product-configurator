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
            'attr_qty_prefix': '__attribute_qty-',
            'subattr_qty_prefix': '__subproduct_qty-',
        })
        return res

    @api.model
    def get_qty_fields(self, product_tmpl):
        """Add quantity fields for attribute lines that have quantity selection
        enabled"""
        res = {}
        attr_qty_prefix = self._prefixes.get('attr_qty_prefix')
        qty_attr_lines = product_tmpl.attribute_line_ids.filtered(
            lambda l: l.quantity and not l.multi)
        for line in qty_attr_lines:
            attribute = line.attribute_id
            default_attrs = self.get_field_default_attrs()

            res[attr_qty_prefix + str(attribute.id)] = dict(
                default_attrs,
                type='integer',
                string='Quantity',
                sequence=line.sequence,
            )
        return res

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form',
    #                     toolbar=False, submenu=False):
    #     subattr_qty_prefix = self._prefixes.get('subattr_qty_prefix')

    @api.model
    def add_qty_fields(self, wiz, xml_view, fields):
        """Add quantity fields to view after each dynamic field"""
        attr_qty_prefix = self._prefixes.get('attr_qty_prefix')
        field_prefix = self._prefixes.get('field_prefix')
        qty_fields = [f for f in fields if f.startswith(attr_qty_prefix)]
        for qty_field in qty_fields:
            # If the matching attribute field is found in the view add after
            attr_id = int(qty_field.replace(attr_qty_prefix, ''))
            dynamic_field_name = field_prefix + str(attr_id)
            dynamic_field = xml_view.xpath(
                "//field[@name='%s']" % dynamic_field_name)
            if not dynamic_field:
                continue

            active_step = wiz.get_active_step()

            available_attr_ids = active_step.attribute_line_ids.mapped(
                'attribute_id').ids

            if attr_id not in available_attr_ids:
                continue

            qty_field = etree.Element(
                'field',
                name=qty_field,
                attrs=str({
                    'invisible': [
                        '|',
                        (dynamic_field_name, '=', False)],

                })
            )
            orm.setup_modifiers(qty_field)
            dynamic_form = dynamic_field[0].getparent()
            dynamic_form.insert(
                dynamic_form.index(dynamic_field[0]) + 1, qty_field
            )
        return xml_view
