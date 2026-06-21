from odoo import models, fields, api


class PriceMonitorRecord(models.Model):
    _name = 'price.monitor.record'
    _description = '价格监控记录'
    _order = 'check_date desc'

    monitor_product_id = fields.Many2one(
        'price.monitor.product',
        string='监控商品',
        required=True,
        ondelete='cascade',
    )
    check_date = fields.Date(
        string='检查日期',
        required=True,
        default=fields.Date.context_today,
    )
    competitor_price = fields.Float(
        string='竞品价格',
        digits='Product Price',
        required=True,
    )
    our_price = fields.Float(
        string='我方价格',
        digits='Product Price',
    )
    price_diff = fields.Float(
        string='价差',
        digits='Product Price',
        compute='_compute_price_diff',
        store=True,
    )
    price_diff_rate = fields.Float(
        string='价差率(%)',
        digits=(16, 2),
        compute='_compute_price_diff',
        store=True,
    )
    alert_type = fields.Selection(
        selection=[
            ('none', '无'),
            ('competitor_drop', '竞品降价'),
            ('competitor_rise', '竞品涨价'),
            ('opportunity', '价格机会'),
        ],
        string='预警类型',
        default='none',
    )
    notes = fields.Text(
        string='备注',
    )

    @api.depends('our_price', 'competitor_price')
    def _compute_price_diff(self):
        for record in self:
            record.price_diff = record.our_price - record.competitor_price
            if record.competitor_price:
                record.price_diff_rate = (record.our_price - record.competitor_price) / record.competitor_price * 100
            else:
                record.price_diff_rate = 0.0
