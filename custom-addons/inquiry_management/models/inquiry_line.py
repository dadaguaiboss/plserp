# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InquiryOrderLine(models.Model):
    _name = 'inquiry.order.line'
    _description = '询单明细'
    _order = 'sequence, id'

    sequence = fields.Integer(string='排序', default=10)
    inquiry_id = fields.Many2one(
        'inquiry.order',
        string='询单',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='产品',
        required=True,
    )
    qty = fields.Float(
        string='数量',
        default=1.0,
        required=True,
    )
    currency_id = fields.Many2one(
        related='inquiry_id.currency_id',
        store=True,
    )

    # ------ 价格 ------
    supplier_price = fields.Float(
        string='供应商报价',
        digits='Product Price',
    )
    last_purchase_price = fields.Float(
        string='上次采购价',
        compute='_compute_last_purchase_price',
        store=True,
        digits='Product Price',
    )
    price_change_rate = fields.Float(
        string='价格变化率 (%)',
        compute='_compute_price_change_rate',
        store=True,
        digits=(16, 2),
    )
    suggested_sale_price = fields.Float(
        string='建议销售价',
        digits='Product Price',
    )

    # ------ 成本 ------
    logistics_cost = fields.Float(
        string='物流成本',
        digits='Product Price',
    )
    platform_commission_rate = fields.Float(
        string='平台佣金率 (%)',
        digits=(16, 2),
        default=5.0,
    )
    platform_commission = fields.Monetary(
        string='平台佣金',
        compute='_compute_platform_commission',
        store=True,
        currency_field='currency_id',
    )
    packaging_cost = fields.Float(
        string='包装成本',
        digits='Product Price',
    )
    other_cost = fields.Float(
        string='其他成本',
        digits='Product Price',
    )

    # ------ 利润计算 ------
    total_cost = fields.Monetary(
        string='总成本',
        compute='_compute_profit',
        store=True,
        currency_field='currency_id',
    )
    profit = fields.Monetary(
        string='毛利',
        compute='_compute_profit',
        store=True,
        currency_field='currency_id',
    )
    margin_rate = fields.Float(
        string='毛利率 (%)',
        compute='_compute_profit',
        store=True,
        digits=(16, 2),
    )
    is_profitable = fields.Boolean(
        string='可采',
        compute='_compute_profit',
        store=True,
    )

    # ==================== 计算方法 ====================

    @api.depends('product_id', 'inquiry_id.partner_id')
    def _compute_last_purchase_price(self):
        """获取上次采购价"""
        for line in self:
            last_price = 0.0
            if line.product_id:
                # 查找该产品最近一条已确认的采购订单行
                last_po_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', line.product_id.id),
                    ('order_id.state', 'in', ['purchase', 'done']),
                ], order='create_date desc', limit=1)
                if last_po_line:
                    last_price = last_po_line.price_unit
            line.last_purchase_price = last_price

    @api.depends('supplier_price', 'last_purchase_price')
    def _compute_price_change_rate(self):
        """计算价格变化率"""
        for line in self:
            if line.last_purchase_price:
                line.price_change_rate = (
                    (line.supplier_price - line.last_purchase_price)
                    / line.last_purchase_price * 100
                )
            else:
                line.price_change_rate = 0.0

    @api.depends('suggested_sale_price', 'platform_commission_rate')
    def _compute_platform_commission(self):
        """计算平台佣金"""
        for line in self:
            line.platform_commission = (
                line.suggested_sale_price * line.platform_commission_rate / 100
            )

    @api.depends(
        'supplier_price',
        'logistics_cost',
        'platform_commission',
        'packaging_cost',
        'other_cost',
        'suggested_sale_price',
    )
    def _compute_profit(self):
        """计算总成本、毛利、毛利率"""
        for line in self:
            total_cost = (
                line.supplier_price
                + line.logistics_cost
                + line.platform_commission
                + line.packaging_cost
                + line.other_cost
            )
            profit = line.suggested_sale_price - total_cost
            margin_rate = (
                (profit / line.suggested_sale_price * 100)
                if line.suggested_sale_price else 0.0
            )
            line.total_cost = total_cost
            line.profit = profit
            line.margin_rate = margin_rate
            line.is_profitable = profit > 0
