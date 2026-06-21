# Part of ProLion ERP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    unified_social_credit_code = fields.Char(
        string='统一社会信用代码',
        size=18,
    )
    invoice_title = fields.Char(
        string='发票抬头',
    )
    bank_name = fields.Char(
        string='开户银行',
    )
    bank_account = fields.Char(
        string='银行账号',
    )
