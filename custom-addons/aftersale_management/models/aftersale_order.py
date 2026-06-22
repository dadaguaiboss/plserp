# Part of PLS ERP. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class AftersaleOrder(models.Model):
    _name = 'aftersale.order'
    _description = '售后单'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='售后单号',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('新建'),
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='关联销售订单',
        tracking=True,
    )
    platform = fields.Selection(
        selection=[
            ('taobao', '淘宝'),
            ('tmall', '天猫'),
            ('jd', '京东'),
            ('pdd', '拼多多'),
            ('douyin', '抖音'),
            ('kuaishou', '快手'),
            ('wechat', '微信小程序'),
            ('offline', '线下'),
            ('other', '其他'),
        ],
        string='平台',
        tracking=True,
    )
    platform_order_no = fields.Char(string='平台订单号', tracking=True)
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
    aftersale_type = fields.Selection(
        selection=[
            ('return', '退货'),
            ('exchange', '换货'),
            ('refund', '退款'),
            ('resend', '补发'),
        ],
        string='售后类型',
        required=True,
        default='return',
        tracking=True,
    )
    reason_category = fields.Selection(
        selection=[
            ('no_reason_7day', '7天无理由'),
            ('quality', '质量问题'),
            ('wrong_item', '发错货'),
            ('damaged', '运输破损'),
            ('size_issue', '尺码问题'),
            ('other', '其他'),
        ],
        string='原因类别',
        required=True,
        tracking=True,
    )
    reason_detail = fields.Text(string='详细原因')
    has_images = fields.Boolean(string='是否有图片', default=False)
    amount_total = fields.Monetary(
        string='订单金额',
        currency_field='currency_id',
    )
    refund_amount = fields.Monetary(
        string='退款金额',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='币种',
        default=lambda self: self.env.company.currency_id.id,
    )
    state = fields.Selection(
        selection=[
            ('draft', '草稿'),
            ('pending_review', '待审核'),
            ('auto_approved', '自动审核通过'),
            ('manual_review', '人工复核'),
            ('approved', '已批准'),
            ('rejected', '已拒绝'),
            ('completed', '已完成'),
        ],
        string='状态',
        default='draft',
        required=True,
        tracking=True,
    )
    review_mode = fields.Selection(
        selection=[
            ('auto', '自动审核'),
            ('manual', '人工审核'),
        ],
        string='审核方式',
        readonly=True,
    )
    review_result = fields.Text(string='审核结果')
    reviewer_id = fields.Many2one(
        'res.users',
        string='审核人',
        readonly=True,
    )
    review_date = fields.Datetime(string='审核时间', readonly=True)
    tracking_number_return = fields.Char(string='退货物流单号', tracking=True)
    warehouse_verified = fields.Boolean(
        string='仓库已核验',
        default=False,
    )
    warehouse_verify_date = fields.Datetime(
        string='仓库核验时间',
        readonly=True,
    )
    warehouse_notes = fields.Text(string='仓库备注')
    line_ids = fields.One2many(
        'aftersale.order.line',
        'aftersale_id',
        string='售后明细',
    )
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        default=lambda self: self.env.company,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('新建')) == _('新建'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'aftersale.order'
                ) or _('新建')
        return super().create(vals_list)

    def action_submit(self):
        """提交售后申请"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('只有草稿状态的售后单才能提交。'))
            record.state = 'pending_review'
            record.action_auto_review()

    def action_auto_review(self):
        """自动审核规则引擎"""
        self.ensure_one()
        if self.state != 'pending_review':
            return

        rules = self.env['aftersale.rule'].search(
            [('active', '=', True)],
            order='sequence',
        )

        for rule in rules:
            matched, result = rule._evaluate(self)
            if matched:
                self.review_mode = 'auto'
                if result == 'auto_approve':
                    self.state = 'auto_approved'
                    self.review_result = _(
                        '自动审核通过 - 规则: %s'
                    ) % rule.name
                    self.review_date = fields.Datetime.now()
                elif result == 'manual_review':
                    self.state = 'manual_review'
                    self.review_result = _(
                        '需人工复核 - 规则: %s'
                    ) % rule.name
                self.message_post(
                    body=_('自动审核结果: %s') % self.review_result,
                )
                return

        # 未匹配任何规则，转人工审核
        self.state = 'manual_review'
        self.review_mode = 'manual'
        self.review_result = _('未匹配自动审核规则，转人工审核')
        self.message_post(body=self.review_result)

    def action_approve(self):
        """审核通过"""
        for record in self:
            if record.state not in ('auto_approved', 'manual_review'):
                raise UserError(_('当前状态不允许审核通过。'))
            record.write({
                'state': 'approved',
                'reviewer_id': self.env.uid,
                'review_date': fields.Datetime.now(),
            })
            record.message_post(body=_('售后单已审核通过。'))

    def action_reject(self):
        """审核拒绝"""
        for record in self:
            if record.state not in ('auto_approved', 'manual_review'):
                raise UserError(_('当前状态不允许拒绝。'))
            record.write({
                'state': 'rejected',
                'reviewer_id': self.env.uid,
                'review_date': fields.Datetime.now(),
            })
            record.message_post(body=_('售后单已拒绝。'))

    def action_complete(self):
        """完成售后"""
        for record in self:
            if record.state != 'approved':
                raise UserError(_('只有已批准的售后单才能完成。'))
            record.state = 'completed'
            record.message_post(body=_('售后单已完成。'))

    def action_warehouse_verify(self):
        """仓库核验"""
        for record in self:
            record.write({
                'warehouse_verified': True,
                'warehouse_verify_date': fields.Datetime.now(),
            })
            record.message_post(body=_('仓库已完成核验。'))
