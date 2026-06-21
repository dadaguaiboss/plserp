# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InquiryOrder(models.Model):
    _name = 'inquiry.order'
    _description = '询单'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'inquiry_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='询单编号',
        required=True,
        readonly=True,
        default='New',
        copy=False,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='供应商',
        domain=[('supplier_rank', '>', 0)],
        required=True,
        tracking=True,
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='品牌',
        tracking=True,
    )
    user_id = fields.Many2one(
        'res.users',
        string='负责人',
        default=lambda self: self.env.user,
        tracking=True,
    )
    inquiry_date = fields.Date(
        string='询单日期',
        default=fields.Date.context_today,
        tracking=True,
    )
    order_type = fields.Selection(
        selection=[
            ('spot', '现货'),
            ('futures', '期货'),
        ],
        string='类型',
        default='spot',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', '草稿'),
            ('analyzing', '分析中'),
            ('decided', '已决策'),
            ('converted', '已转单'),
            ('archived', '已归档'),
        ],
        string='状态',
        default='draft',
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        'inquiry.order.line',
        'inquiry_id',
        string='询单明细',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='币种',
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        default=lambda self: self.env.company,
    )
    notes = fields.Text(string='备注')

    # ------ 汇总计算 ------
    total_cost = fields.Monetary(
        string='总成本',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    total_profit = fields.Monetary(
        string='总毛利',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
    )
    avg_margin_rate = fields.Float(
        string='平均毛利率 (%)',
        compute='_compute_totals',
        store=True,
        digits=(16, 2),
    )
    line_count = fields.Integer(
        string='明细行数',
        compute='_compute_line_count',
    )

    @api.depends('line_ids')
    def _compute_line_count(self):
        for order in self:
            order.line_count = len(order.line_ids)

    @api.depends(
        'line_ids.total_cost',
        'line_ids.profit',
        'line_ids.suggested_sale_price',
        'line_ids.qty',
    )
    def _compute_totals(self):
        for order in self:
            total_cost = sum(order.line_ids.mapped(lambda l: l.total_cost * l.qty))
            total_revenue = sum(order.line_ids.mapped(lambda l: l.suggested_sale_price * l.qty))
            total_profit = total_revenue - total_cost
            order.total_cost = total_cost
            order.total_profit = total_profit
            order.avg_margin_rate = (total_profit / total_revenue * 100) if total_revenue else 0.0

    # ==================== CRUD ====================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('inquiry.order') or 'New'
        return super().create(vals_list)

    # ==================== 动作 ====================

    def action_analyze(self):
        """开始分析"""
        for order in self:
            if order.state != 'draft':
                raise UserError(_('只有草稿状态的询单可以进入分析。'))
            if not order.line_ids:
                raise UserError(_('请先添加询单明细。'))
            # 触发各行的价格对比计算
            order.line_ids._compute_last_purchase_price()
            order.state = 'analyzing'

    def action_decide(self):
        """确认决策"""
        for order in self:
            if order.state != 'analyzing':
                raise UserError(_('只有分析中的询单可以进行决策。'))
            order.state = 'decided'

    def action_convert_to_preorder(self):
        """转预采订单"""
        for order in self:
            if order.state != 'decided':
                raise UserError(_('只有已决策的询单可以转预采订单。'))

            profitable_lines = order.line_ids.filtered('is_profitable')
            if not profitable_lines:
                raise UserError(_('没有可采的明细行（毛利为正），无法转预采订单。'))

            # 查找预采订单模型（来自 purchase_preorder 模块）
            PreOrder = self.env.get('purchase.preorder')
            if PreOrder is None:
                raise UserError(_('预采订单模块未安装，无法转单。'))

            preorder_lines = []
            for line in profitable_lines:
                preorder_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty,
                    'price_unit': line.supplier_price,
                }))

            preorder = PreOrder.create({
                'partner_id': order.partner_id.id,
                'brand_id': order.brand_id.id if order.brand_id else False,
                'origin': order.name,
                'order_line': preorder_lines,
            })

            order.state = 'converted'

            return {
                'type': 'ir.actions.act_window',
                'name': _('预采订单'),
                'res_model': 'purchase.preorder',
                'res_id': preorder.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_archive_record(self):
        """归档"""
        for order in self:
            order.state = 'archived'

    def action_reset_to_draft(self):
        """重置为草稿"""
        for order in self:
            if order.state not in ('analyzing', 'archived'):
                raise UserError(_('只有分析中或已归档的询单可以重置为草稿。'))
            order.state = 'draft'
