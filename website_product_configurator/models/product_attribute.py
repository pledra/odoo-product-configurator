from odoo import api, fields, models


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    invisible = fields.Boolean(
        string="Invisible",
        help="Set in order to make attribute invisible, "
        "when there is no available attribute values, in the configuration "
        "interface"
    )


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    invisible = fields.Boolean(
        string="Invisible",
        help="Set in order to make attribute invisible, "
        "when there is no available attribute values, in the configuration "
        "interface"
    )

    @api.onchange("attribute_id")
    def onchange_attribute(self):
        res = super(ProductAttributeLine, self).onchange_attribute()
        self.invisible = self.attribute_id.invisible
        return res
