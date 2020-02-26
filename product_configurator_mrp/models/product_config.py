from odoo import models


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def create_get_bom(self, variant, product_tmpl_id=None, values=None):
        if values is None:
            values = {}
        if (
            product_tmpl_id is None
            or variant.product_tmpl_id != product_tmpl_id
        ):
            product_tmpl_id = variant.product_tmpl_id

        model_name = "mrp.bom"
        mrpBom = self.env[model_name]
        attr_products = variant.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id.product_id"
        )
        existing_bom = self.env[model_name].search(
            [
                ("product_tmpl_id", "=", product_tmpl_id.id),
                ("product_id", "=", variant.id),
                ("bom_line_ids.product_id", "in", attr_products.ids),
            ]
        )
        existing_bom = existing_bom.filtered(
            lambda bom: len(bom.bom_line_ids) == len(attr_products)
        )
        if existing_bom:
            return existing_bom[:1]

        bom_lines = []
        bom_line_model = "mrp.bom.line"
        mrpBomLine = self.env[bom_line_model]
        for product in attr_products:
            bom_line_vals = {"product_id": product.id}
            specs = self.get_onchange_specifications(model=bom_line_model)
            updates = mrpBomLine.onchange(bom_line_vals, ["product_id"], specs)
            values = updates.get("value", {})
            values = self.get_vals_to_write(
                values=values, model=bom_line_model
            )
            values.update(bom_line_vals)
            bom_lines.append((0, 0, values))

        bom_values = {
            "product_tmpl_id": self.product_tmpl_id.id,
            "product_id": variant.id,
            "bom_line_ids": bom_lines,
        }
        specs = self.get_onchange_specifications(model=model_name)
        updates = mrpBom.onchange(
            bom_values,
            ["product_id", "product_tmpl_id", "bom_line_ids"],
            specs,
        )
        values = updates.get("value", {})
        values = self.get_vals_to_write(values=values, model=model_name)
        values.update(bom_values)
        mrp_bom_id = mrpBom.create(values)
        return mrp_bom_id

    def create_get_variant(self, value_ids=None, custom_vals=None):
        variant = super(ProductConfigSession, self).create_get_variant(
            value_ids=value_ids, custom_vals=custom_vals
        )
        self.create_get_bom(
            variant=variant, product_tmpl_id=self.product_tmpl_id
        )
        return variant
