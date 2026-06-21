# -*- coding: utf-8 -*-
{
    'name': 'OMS订单管理',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': '多平台订单统一管理：采集、解析、审核、发货、物流跟踪',
    'description': """
OMS订单管理模块
================
- 统一采集多平台订单（天猫/京东/抖音/拼多多/小红书/Amazon/Shopee/Lazada）
- 订单解析、自动匹配产品、审核
- 发货管理、物流状态跟踪
- 关联销售订单
    """,
    'author': '普洛狮科技',
    'website': 'https://www.prolion-erp.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'stock',
        'product',
        'mail',
        'delivery',
        'purchase_preorder',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/oms_order_views.xml',
        'views/menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
