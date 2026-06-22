# -*- coding: utf-8 -*-
{
    'name': '询单管理',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': '供应商报价询单、价格对比、利润测算、配货分析',
    'description': """
询单管理模块
=============
- 收到供应商报价，区分现货/期货
- 与历史采购价对比，标识价格变化
- 配货对比（多供应商组合）
- 利润测算，自动计算毛利率
- 一键转预采订单
    """,
    'author': '普洛狮科技',
    'website': 'https://www.pls-erp.com',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'product',
        'sale',
        'mail',
        'purchase_preorder',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/inquiry_order_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
