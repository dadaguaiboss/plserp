# Part of ProLion ERP. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class HeadlessPackage(models.Model):
    _name = 'headless.package'
    _description = '无头件'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'receive_date desc, id desc'

    name = fields.Char(
        string='无头件编号',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('新建'),
    )
    tracking_number = fields.Char(
        string='物流单号',
        required=True,
        tracking=True,
    )
    sender_name = fields.Char(string='寄件人', tracking=True)
    sender_phone = fields.Char(string='寄件人电话', tracking=True)
    product_description = fields.Text(string='商品描述')
    product_ids = fields.Many2many(
        'product.product',
        'headless_package_product_rel',
        'headless_id',
        'product_id',
        string='匹配产品',
    )
    qty = fields.Float(string='数量', default=1.0)
    receive_date = fields.Date(
        string='收件日期',
        default=fields.Date.context_today,
        tracking=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='仓库',
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('new', '新建'),
            ('matching', '匹配中'),
            ('matched', '已匹配'),
            ('confirmed', '已确认'),
            ('processed', '已处理'),
            ('expired', '已过期'),
        ],
        string='状态',
        default='new',
        required=True,
        tracking=True,
    )
    match_confidence = fields.Selection(
        selection=[
            ('high', '高'),
            ('medium', '中'),
            ('low', '低'),
            ('none', '未匹配'),
        ],
        string='匹配置信度',
        default='none',
    )
    matched_sale_order_id = fields.Many2one(
        'sale.order',
        string='匹配销售订单',
        tracking=True,
    )
    matched_aftersale_id = fields.Many2one(
        'aftersale.order',
        string='匹配售后单',
        tracking=True,
    )
    match_method = fields.Selection(
        selection=[
            ('tracking', '物流单号匹配'),
            ('phone', '手机号匹配'),
            ('sku', 'SKU匹配'),
            ('manual', '人工匹配'),
        ],
        string='匹配方式',
    )
    notes = fields.Text(string='备注')
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
                    'headless.package'
                ) or _('新建')
        return super().create(vals_list)

    def action_auto_match(self):
        """自动匹配算法"""
        for record in self:
            if record.state not in ('new', 'matching'):
                continue

            record.state = 'matching'

            # 1. 物流单号精确匹配 → 高置信度
            if record.tracking_number:
                aftersale = self.env['aftersale.order'].search([
                    ('tracking_number_return', '=', record.tracking_number),
                ], limit=1)
                if aftersale:
                    record.write({
                        'matched_aftersale_id': aftersale.id,
                        'matched_sale_order_id': aftersale.sale_order_id.id,
                        'match_confidence': 'high',
                        'match_method': 'tracking',
                        'state': 'matched',
                    })
                    record.message_post(
                        body=_('物流单号精确匹配成功，关联售后单: %s') % aftersale.name,
                    )
                    continue

            # 2. 手机号模糊匹配 → 中置信度
            if record.sender_phone:
                phone_suffix = record.sender_phone[-4:] if len(record.sender_phone) >= 4 else record.sender_phone
                partners = self.env['res.partner'].search([
                    ('phone', 'like', '%' + phone_suffix),
                ])
                if not partners:
                    partners = self.env['res.partner'].search([
                        ('mobile', 'like', '%' + phone_suffix),
                    ])
                if partners:
                    sale_orders = self.env['sale.order'].search([
                        ('partner_id', 'in', partners.ids),
                        ('state', 'in', ('sale', 'done')),
                    ], order='date_order desc', limit=1)
                    if sale_orders:
                        record.write({
                            'matched_sale_order_id': sale_orders.id,
                            'match_confidence': 'medium',
                            'match_method': 'phone',
                            'state': 'matched',
                        })
                        record.message_post(
                            body=_('手机号模糊匹配成功，关联销售订单: %s') % sale_orders.name,
                        )
                        continue

            # 3. SKU匹配 → 低置信度
            if record.product_ids:
                sale_lines = self.env['sale.order.line'].search([
                    ('product_id', 'in', record.product_ids.ids),
                    ('order_id.state', 'in', ('sale', 'done')),
                ], order='create_date desc', limit=1)
                if sale_lines:
                    record.write({
                        'matched_sale_order_id': sale_lines.order_id.id,
                        'match_confidence': 'low',
                        'match_method': 'sku',
                        'state': 'matched',
                    })
                    record.message_post(
                        body=_('SKU匹配成功，关联销售订单: %s') % sale_lines.order_id.name,
                    )
                    continue

            # 未匹配
            record.write({
                'match_confidence': 'none',
                'state': 'new',
            })
            record.message_post(body=_('自动匹配未找到关联订单。'))

    def action_confirm_match(self):
        """确认匹配"""
        for record in self:
            if record.state != 'matched':
                raise UserError(_('只有已匹配状态的无头件才能确认。'))
            record.state = 'confirmed'
            record.message_post(body=_('匹配已确认。'))

    def action_create_aftersale(self):
        """创建售后单"""
        self.ensure_one()
        if self.state not in ('confirmed', 'matched'):
            raise UserError(_('请先确认匹配后再创建售后单。'))

        vals = {
            'sale_order_id': self.matched_sale_order_id.id,
            'partner_id': self.matched_sale_order_id.partner_id.id if self.matched_sale_order_id else False,
            'aftersale_type': 'return',
            'reason_category': 'other',
            'reason_detail': _('由无头件 %s 创建') % self.name,
            'tracking_number_return': self.tracking_number,
        }
        aftersale = self.env['aftersale.order'].create(vals)

        # 添加产品明细
        for product in self.product_ids:
            self.env['aftersale.order.line'].create({
                'aftersale_id': aftersale.id,
                'product_id': product.id,
                'product_qty': self.qty,
            })

        self.write({
            'matched_aftersale_id': aftersale.id,
            'state': 'processed',
        })
        self.message_post(
            body=_('已创建售后单: %s') % aftersale.name,
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'aftersale.order',
            'res_id': aftersale.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_expire(self):
        """过期处理"""
        for record in self:
            record.state = 'expired'
            record.message_post(body=_('无头件已过期。'))

    @api.model
    def _cron_expire_old_packages(self):
        """定时任务：超90天未匹配自动清理"""
        expire_date = fields.Date.today() - timedelta(days=90)
        old_packages = self.search([
            ('state', 'in', ('new', 'matching')),
            ('receive_date', '<=', expire_date),
        ])
        for pkg in old_packages:
            pkg.action_expire()
        return True
