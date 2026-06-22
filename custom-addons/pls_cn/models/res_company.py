# Part of PLS ERP. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    unified_social_credit_code = fields.Char(
        string='统一社会信用代码',
        size=18,
        help='企业统一社会信用代码（18位）',
    )
    bank_name = fields.Char(
        string='开户银行',
    )
    bank_account_name = fields.Char(
        string='开户名称',
    )
    bank_account_number = fields.Char(
        string='银行账号',
    )
    legal_representative = fields.Char(
        string='法定代表人',
    )
    registered_capital = fields.Char(
        string='注册资本',
    )
    business_scope = fields.Text(
        string='经营范围',
    )
