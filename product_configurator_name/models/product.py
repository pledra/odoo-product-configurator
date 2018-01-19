# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    name_override = fields.Char('Custom Name')
    hidden_attribute_value_ids = fields.Many2many('product.attribute.value', string='Hidden Attributes', compute='_compute_hidden')

    def _compute_hidden(self):
        for product in self:
            hidden_ids = self.env['product.attribute.value']
            for line in product.attribute_line_ids.sorted('sequence'):
                if line.display_mode == 'hide':
                    key = line.attribute_id.name
                    for value in product.attribute_value_ids:
                        if value.attribute_id.name == key:
                            hidden_ids += value
            product.hidden_attribute_value_ids = hidden_ids

    @api.multi
    def name_get(self):
        """ Override variant name
        """

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []
        for product in self.sudo():
            # START CHANGES
            if product.name_override:
                name = product.name_override
            else:
                if product.config_ok:
                    # prefetch values
                    value_dict = {}
                    for value in product.attribute_value_ids:
                        old_value = value_dict.get(value.attribute_id.name)
                        if old_value:
                            value_dict[value.attribute_id.name] = ', '.join([old_value, value.name])
                        else:
                            value_dict[value.attribute_id.name] = value.name
                    # assemble variant
                    name_elements = []
                    for line in product.attribute_line_ids.sorted('sequence'):
                        if line.display_mode == 'hide':
                            continue
                        key = line.attribute_id.name
                        if key in value_dict:
                            value = value_dict[key]
                        else:
                             continue
                        if line.display_mode == 'value':
                            name_elements.append(u'{}'.format(value))
                        elif line.display_mode == 'attribute':
                            name_elements.append(u'{}: {}'.format(key, value))
                    variant = ', '.join(name_elements)
                else:
                    # display only the attributes with multiple possible values on the template
                    variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
                    variant = product.attribute_value_ids._variant_name(variable_attributes)

                name = variant and "%s (%s)" % (product.name, variant) or product.name
            # END CHANGES
            sellers = []
            if partner_ids:
                sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
                if not sellers:
                    sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
