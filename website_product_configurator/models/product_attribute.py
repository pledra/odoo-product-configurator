from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    hide = fields.Boolean(
        string="Invisible",
        help="Set in order to make attribute invisible, "
        "when there is no available attribute values, in the configuration "
        "interface"
    )


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    hide = fields.Boolean(
        string="Invisible",
        help="Set in order to make attribute invisible, "
        "when there is no available attribute values, in the configuration "
        "interface"
    )

    @api.onchange("attribute_id")
    def onchange_attribute(self):
        res = super(ProductAttributeLine, self).onchange_attribute()
        self.hide = self.attribute_id.hide
        return res
