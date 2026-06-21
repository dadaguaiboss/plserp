# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchasePreorder(models.Model):
    _name = 'purchase.preorder'
    _description = '预采订单'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='订单编号',
        required=True,
        copy=False,
        readonly=True,
        default='新建',
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='品牌',
        required=True,
        tracking=True,
    )
    purchase_mode = fields.Selection(
        selection=[
            ('self_purchase', '自采'),
            ('general_trade', '大贸'),
        ],
        string='采购模式',
        required=True,
        default='self_purchase',
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='供应商',
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
    )
    user_id = fields.Many2one(
        'res.users',
        string='采购员',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    order_type = fields.Selection(
        selection=[
            ('spot', '现货'),
            ('futures', '期货'),
        ],
        string='订单类型',
        required=True,
        default='spot',
        tracking=True,
    )
    expected_date = fields.Date(
        string='预计到货日期',
        tracking=True,
    )
    target_platform = fields.Selection(
        selection=[
            ('tmall', '天猫'),
            ('jd', '京东'),
            ('douyin', '抖音'),
            ('pdd', '拼多多'),
            ('offline', '线下'),
            ('other', '其他'),
        ],
        string='目标平台',
        tracking=True,
    )
    payment_terms = fields.Char(
        string='付款条款',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', '草稿'),
            ('submitted', '已提交'),
            ('approved', '已审批'),
            ('converted', '已转采购单'),
            ('cancelled', '已取消'),
        ],
        string='状态',
        default='draft',
        required=True,
        tracking=True,
        copy=False,
    )
    line_ids = fields.One2many(
        'purchase.preorder.line',
        'preorder_id',
        string='订单明细',
        copy=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        required=True,
        default=lambda self: self.env.company,
    )
    notes = fields.Html(string='备注')
    amount_total = fields.Monetary(
        string='合计金额',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='币种',
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'preorder_id',
        string='关联采购单',
    )
    purchase_order_count = fields.Integer(
        string='采购单数量',
        compute='_compute_purchase_order_count',
    )
    submitted_date = fields.Datetime(string='提交日期', readonly=True, copy=False)
    approved_date = fields.Datetime(string='审批日期', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='审批人', readonly=True, copy=False)

    @api.depends('line_ids.price_subtotal')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped('price_subtotal'))

    def _compute_purchase_order_count(self):
        for order in self:
            order.purchase_order_count = len(order.purchase_order_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '新建') == '新建':
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.preorder') or '新建'
        return super().create(vals_list)

    def action_submit(self):
        """提交预采订单"""
        for order in self:
            if not order.line_ids:
                raise UserError(_('请至少添加一行订单明细！'))
            if order.order_type == 'futures':
                if not order.expected_date:
                    raise UserError(_('期货订单必须填写预计到货日期！'))
                if not order.target_platform:
                    raise UserError(_('期货订单必须选择目标平台！'))
            order.write({
                'state': 'submitted',
                'submitted_date': fields.Datetime.now(),
            })

    def action_approve(self):
        """审批预采订单 - 谁做谁审"""
        for order in self:
            if order.user_id != self.env.user:
                raise UserError(_(
                    '审批机制为"谁做谁审"，只有采购员 %s 本人可以审批此订单！',
                    order.user_id.name,
                ))
            order.write({
                'state': 'approved',
                'approved_date': fields.Datetime.now(),
                'approved_by': self.env.user.id,
            })

    def action_convert_to_purchase(self):
        """将预采订单转为正式采购单"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('只有已审批的预采订单才能转为正式采购单！'))

        po_lines = []
        for line in self.line_ids:
            qty_to_order = line.qty_remaining
            if qty_to_order <= 0:
                continue
            po_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': qty_to_order,
                'price_unit': line.price_unit,
                'name': line.product_id.display_name,
                'product_uom': line.product_id.uom_po_id.id or line.product_id.uom_id.id,
                'date_planned': self.expected_date or fields.Date.context_today(self),
            }))

        if not po_lines:
            raise UserError(_('没有需要采购的数量（所有产品已到货）！'))

        po_vals = {
            'partner_id': self.partner_id.id,
            'preorder_id': self.id,
            'order_line': po_lines,
            'notes': self.notes,
            'company_id': self.company_id.id,
            'user_id': self.user_id.id,
        }
        purchase_order = self.env['purchase.order'].create(po_vals)

        self.write({'state': 'converted'})

        return {
            'type': 'ir.actions.act_window',
            'name': _('采购单'),
            'res_model': 'purchase.order',
            'res_id': purchase_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """取消预采订单"""
        for order in self:
            if order.state == 'converted':
                raise UserError(_('已转为采购单的预采订单不能取消！'))
            order.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """重置为草稿"""
        for order in self:
            if order.state == 'converted':
                raise UserError(_('已转为采购单的预采订单不能重置！'))
            order.write({'state': 'draft'})

    def action_view_purchase_orders(self):
        """查看关联的采购单"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('关联采购单'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('preorder_id', '=', self.id)],
            'context': {'default_preorder_id': self.id},
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    preorder_id = fields.Many2one(
        'purchase.preorder',
        string='预采订单',
        copy=False,
    )
