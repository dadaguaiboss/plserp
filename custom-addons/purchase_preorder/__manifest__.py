# -*- coding: utf-8 -*-
{
    'name': '预采订单管理',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': '预采订单（拟下单）管理，支持自采/大贸、期货/现货、审批流转及转正式采购单',
    'description': """
        预采订单管理模块
        ================
        - 5人负责5个品牌，每人独立管理各自品牌的采购
        - 采购模式：自采和大贸
        - 预采订单（拟下单）→ 审批 → 转正式采购单
        - 审批机制："谁做谁审"
        - 支持期货/现货标记
        - 期货需填写预计到货日期和目标平台
        - 部分到货支持
        - 入库加权平均成本（AVCO）
    """,
    'author': '自定义开发',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'purchase',
        'stock',
        'product',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/product_brand_views.xml',
        'views/purchase_preorder_views.xml',
        'views/menu.xml',
        'report/purchase_preorder_report.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
