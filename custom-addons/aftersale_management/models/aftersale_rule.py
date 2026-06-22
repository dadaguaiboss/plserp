# Part of PLS ERP. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import timedelta


class AftersaleRule(models.Model):
    _name = 'aftersale.rule'
    _description = '售后自动审核规则'
    _order = 'sequence, id'

    name = fields.Char(string='规则名称', required=True)
    sequence = fields.Integer(string='顺序', default=10)
    active = fields.Boolean(string='启用', default=True)
    condition_type = fields.Selection(
        selection=[
            ('no_reason_7day', '7天无理由且未使用'),
            ('quality_with_image', '质量问题且有图片'),
            ('over_30days', '超过30天'),
            ('high_value', '高价值订单'),
            ('abnormal_address', '异常地址'),
        ],
        string='条件类型',
        required=True,
    )
    result = fields.Selection(
        selection=[
            ('auto_approve', '自动通过'),
            ('manual_review', '人工复核'),
        ],
        string='审核结果',
        required=True,
    )
    threshold_amount = fields.Float(
        string='金额阈值',
        help='用于高价值订单判断，订单金额超过此阈值时触发规则',
    )
    threshold_days = fields.Integer(
        string='天数阈值',
        help='用于时间相关规则判断',
    )

    def _evaluate(self, aftersale):
        """
        评估规则是否匹配售后单。
        返回 (matched: bool, result: str)
        """
        self.ensure_one()

        if self.condition_type == 'no_reason_7day':
            # 7天无理由 + 未使用 → 自动通过
            if aftersale.reason_category == 'no_reason_7day':
                days = self.threshold_days or 7
                if aftersale.sale_order_id and aftersale.sale_order_id.date_order:
                    delta = fields.Datetime.now() - aftersale.sale_order_id.date_order
                    if delta <= timedelta(days=days):
                        return True, self.result
                else:
                    # 无关联订单日期时仍匹配
                    return True, self.result

        elif self.condition_type == 'quality_with_image':
            # 质量问题 + 有图片 → 自动通过
            if aftersale.reason_category == 'quality' and aftersale.has_images:
                return True, self.result

        elif self.condition_type == 'over_30days':
            # 超过30天 → 人工复核
            days = self.threshold_days or 30
            if aftersale.sale_order_id and aftersale.sale_order_id.date_order:
                delta = fields.Datetime.now() - aftersale.sale_order_id.date_order
                if delta > timedelta(days=days):
                    return True, self.result

        elif self.condition_type == 'high_value':
            # 高价值 > 阈值 → 人工复核
            threshold = self.threshold_amount or 1000.0
            if aftersale.amount_total > threshold:
                return True, self.result

        elif self.condition_type == 'abnormal_address':
            # 异常地址检测（可扩展）
            pass

        return False, ''
