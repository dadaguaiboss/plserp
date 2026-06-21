# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = '产品品牌'
    _order = 'name'

    name = fields.Char(string='品牌名称', required=True)
    code = fields.Char(string='品牌代码')
    active = fields.Boolean(string='有效', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='公司',
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)', '品牌名称在同一公司下必须唯一！'),
    ]
