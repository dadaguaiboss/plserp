from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_status = fields.Selection(
        selection=[
            ('not_paid', '未付款'),
            ('partial', '部分付款'),
            ('paid', '已付款'),
            ('invoiced', '已开票'),
        ],
        string='付款状态',
        default='not_paid',
        tracking=True,
    )
    paid_amount = fields.Monetary(
        string='已付金额',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
    )
    remaining_amount = fields.Monetary(
        string='待付金额',
        currency_field='currency_id',
        compute='_compute_remaining_amount',
        store=True,
    )
    payment_notes = fields.Text(
        string='付款备注',
    )

    @api.depends('amount_total', 'paid_amount')
    def _compute_remaining_amount(self):
        for order in self:
            order.remaining_amount = order.amount_total - order.paid_amount
