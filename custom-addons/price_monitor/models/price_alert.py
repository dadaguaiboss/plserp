from odoo import models, fields


class PriceAlert(models.Model):
    _name = 'price.alert'
    _description = '价格预警'
    _order = 'alert_date desc, severity desc'

    name = fields.Char(
        string='预警标题',
        required=True,
    )
    monitor_product_id = fields.Many2one(
        'price.monitor.product',
        string='监控商品',
        required=True,
        ondelete='cascade',
    )
    alert_type = fields.Selection(
        selection=[
            ('price_drop', '竞品降价'),
            ('price_rise', '竞品涨价'),
            ('opportunity', '价格机会'),
            ('abnormal', '异常波动'),
        ],
        string='预警类型',
        required=True,
    )
    alert_date = fields.Datetime(
        string='预警时间',
        default=fields.Datetime.now,
        required=True,
    )
    message = fields.Text(
        string='预警信息',
    )
    state = fields.Selection(
        selection=[
            ('new', '新预警'),
            ('read', '已读'),
            ('processed', '已处理'),
        ],
        string='状态',
        default='new',
        required=True,
        tracking=True,
    )
    severity = fields.Selection(
        selection=[
            ('low', '低'),
            ('medium', '中'),
            ('high', '高'),
        ],
        string='严重程度',
        default='medium',
        required=True,
    )

    def action_mark_read(self):
        self.write({'state': 'read'})

    def action_mark_processed(self):
        self.write({'state': 'processed'})
