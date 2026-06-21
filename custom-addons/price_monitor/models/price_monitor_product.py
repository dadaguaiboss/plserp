from odoo import models, fields, api


class PriceMonitorProduct(models.Model):
    _name = 'price.monitor.product'
    _description = '价格监控商品'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_check_date desc'

    product_id = fields.Many2one(
        'product.product',
        string='我方商品',
        required=True,
        tracking=True,
    )
    platform = fields.Selection(
        selection=[
            ('taobao', '淘宝'),
            ('jd', '京东'),
            ('pdd', '拼多多'),
            ('amazon', '亚马逊'),
            ('other', '其他'),
        ],
        string='竞品平台',
        required=True,
        tracking=True,
    )
    competitor_name = fields.Char(
        string='竞品名称',
        required=True,
    )
    competitor_url = fields.Char(
        string='竞品链接',
    )
    monitor_frequency = fields.Selection(
        selection=[
            ('daily', '每日'),
            ('weekly', '每周'),
            ('monthly', '每月'),
        ],
        string='监控频率',
        default='daily',
        required=True,
    )
    active = fields.Boolean(
        string='启用',
        default=True,
    )
    our_price = fields.Float(
        string='我方价格',
        digits='Product Price',
    )
    last_check_date = fields.Date(
        string='上次检查日期',
    )
    record_ids = fields.One2many(
        'price.monitor.record',
        'monitor_product_id',
        string='价格记录',
    )

    def name_get(self):
        result = []
        for record in self:
            name = f"[{dict(self._fields['platform'].selection).get(record.platform, '')}] {record.competitor_name}"
            result.append((record.id, name))
        return result
