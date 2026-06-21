# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchasePreorderLine(models.Model):
    _name = 'purchase.preorder.line'
    _description = '预采订单明细行'
    _order = 'sequence, id'

    preorder_id = fields.Many2one(
        'purchase.preorder',
        string='预采订单',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='序号', default=10)
    product_id = fields.Many2one(
        'product.product',
        string='产品',
        required=True,
    )
    product_qty = fields.Float(
        string='预采数量',
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='单位',
        related='product_id.uom_id',
        readonly=True,
    )
    price_unit = fields.Float(
        string='单价',
        required=True,
        digits='Product Price',
    )
    price_subtotal = fields.Monetary(
        string='小计',
        compute='_compute_price_subtotal',
        store=True,
        currency_field='currency_id',
    )
    qty_received = fields.Float(
        string='已到货数量',
        default=0.0,
        digits='Product Unit of Measure',
    )
    qty_remaining = fields.Float(
        string='未到货数量',
        compute='_compute_qty_remaining',
        store=True,
        digits='Product Unit of Measure',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='币种',
        related='preorder_id.currency_id',
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        related='preorder_id.state',
        string='订单状态',
        store=True,
    )

    @api.depends('product_qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit

    @api.depends('product_qty', 'qty_received')
    def _compute_qty_remaining(self):
        for line in self:
            line.qty_remaining = line.product_qty - line.qty_received
