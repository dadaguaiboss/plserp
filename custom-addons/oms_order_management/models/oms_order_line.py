# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OmsOrderLine(models.Model):
    _name = 'oms.order.line'
    _description = '平台订单明细'
    _order = 'sequence, id'

    sequence = fields.Integer(string='排序', default=10)
    order_id = fields.Many2one(
        'oms.order',
        string='平台订单',
        required=True,
        ondelete='cascade',
        index=True,
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
    price_unit = fields.Float(
        string='单价',
        digits='Product Price',
    )
    price_subtotal = fields.Monetary(
        string='小计',
        compute='_compute_price_subtotal',
        store=True,
        currency_field='currency_id',
    )
    platform_sku = fields.Char(
        string='平台SKU编号',
    )
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        store=True,
    )

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit
