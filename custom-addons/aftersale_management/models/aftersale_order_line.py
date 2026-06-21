# Part of ProLion ERP. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class AftersaleOrderLine(models.Model):
    _name = 'aftersale.order.line'
    _description = '售后单明细'

    aftersale_id = fields.Many2one(
        'aftersale.order',
        string='售后单',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product',
        string='产品',
        required=True,
    )
    product_qty = fields.Float(
        string='数量',
        default=1.0,
        required=True,
    )
    price_unit = fields.Float(string='单价')
    reason = fields.Text(string='原因')
