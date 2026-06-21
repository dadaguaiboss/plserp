# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OmsOrder(models.Model):
    _name = 'oms.order'
    _description = '平台订单'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='订单编号',
        required=True,
        readonly=True,
        default='New',
        copy=False,
        tracking=True,
    )
    platform = fields.Selection(
        selection=[
            ('taobao', '天猫/淘宝'),
            ('jd', '京东'),
            ('douyin', '抖音'),
            ('pdd', '拼多多'),
            ('xiaohongshu', '小红书'),
            ('amazon', 'Amazon'),
            ('shopee', 'Shopee'),
            ('lazada', 'Lazada'),
            ('other', '其他'),
        ],
        string='平台',
        required=True,
        default='taobao',
        tracking=True,
    )
    platform_order_no = fields.Char(
        string='平台订单号',
        tracking=True,
        index=True,
    )
    shop_name = fields.Char(
        string='店铺名称',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='客户',
        tracking=True,
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='品牌',
        tracking=True,
    )
    order_date = fields.Datetime(
        string='下单时间',
        default=fields.Datetime.now,
        tracking=True,
    )
    amount_total = fields.Monetary(
        string='订单总额',
        currency_field='currency_id',
        tracking=True,
    )
    shipping_fee = fields.Monetary(
        string='运费',
        currency_field='currency_id',
    )
    commission_fee = fields.Monetary(
        string='平台佣金',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='币种',
        default=lambda self: self.env.company.currency_id,
    )
    state = fields.Selection(
        selection=[
            ('draft', '草稿'),
            ('confirmed', '已确认'),
            ('shipped', '已发货'),
            ('delivered', '已签收'),
            ('cancelled', '已取消'),
            ('after_sale', '售后中'),
        ],
        string='状态',
        default='draft',
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        'oms.order.line',
        'order_id',
        string='订单明细',
    )

    # ------ 收货信息 ------
    shipping_name = fields.Char(string='收货人')
    shipping_phone = fields.Char(string='收货电话')
    shipping_address = fields.Text(string='收货地址')

    # ------ 物流信息 ------
    tracking_number = fields.Char(
        string='物流单号',
        tracking=True,
    )
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='物流公司',
        tracking=True,
    )

    # ------ 关联 ------
    sale_order_id = fields.Many2one(
        'sale.order',
        string='关联销售订单',
        readonly=True,
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        'res.users',
        string='负责人',
        default=lambda self: self.env.user,
        tracking=True,
    )
    notes = fields.Text(string='备注')

    # ------ 计算字段 ------
    line_count = fields.Integer(
        string='明细行数',
        compute='_compute_line_count',
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for order in self:
            order.line_count = len(order.line_ids)

    # ==================== CRUD ====================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('oms.order') or 'New'
        return super().create(vals_list)

    # ==================== 动作 ====================

    def action_confirm(self):
        """确认订单"""
        for order in self:
            if order.state != 'draft':
                raise UserError(_('只有草稿状态的订单可以确认。'))
            order.state = 'confirmed'

    def action_create_sale_order(self):
        """创建关联的销售订单"""
        for order in self:
            if order.state != 'confirmed':
                raise UserError(_('只有已确认的订单可以创建销售订单。'))
            if order.sale_order_id:
                raise UserError(_('该订单已关联销售订单 %s。') % order.sale_order_id.name)
            if not order.partner_id:
                raise UserError(_('请先设置客户信息。'))

            so_lines = []
            for line in order.line_ids:
                so_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'price_unit': line.price_unit,
                }))

            sale_order = self.env['sale.order'].create({
                'partner_id': order.partner_id.id,
                'origin': order.name,
                'order_line': so_lines,
            })
            order.sale_order_id = sale_order.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('销售订单'),
            'res_model': 'sale.order',
            'res_id': self[:1].sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_ship(self):
        """发货"""
        for order in self:
            if order.state != 'confirmed':
                raise UserError(_('只有已确认的订单可以发货。'))
            if not order.tracking_number:
                raise UserError(_('请先填写物流单号。'))
            order.state = 'shipped'

    def action_deliver(self):
        """签收"""
        for order in self:
            if order.state != 'shipped':
                raise UserError(_('只有已发货的订单可以标记为已签收。'))
            order.state = 'delivered'

    def action_cancel(self):
        """取消订单"""
        for order in self:
            if order.state in ('delivered',):
                raise UserError(_('已签收的订单不能取消。'))
            order.state = 'cancelled'

    def action_reset_to_draft(self):
        """重置为草稿"""
        for order in self:
            if order.state != 'cancelled':
                raise UserError(_('只有已取消的订单可以重置为草稿。'))
            order.state = 'draft'

    def action_after_sale(self):
        """标记为售后中"""
        for order in self:
            if order.state not in ('shipped', 'delivered'):
                raise UserError(_('只有已发货或已签收的订单可以发起售后。'))
            order.state = 'after_sale'
