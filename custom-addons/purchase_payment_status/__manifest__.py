{
    'name': '采购付款状态',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'summary': '采购订单付款状态跟踪',
    'description': """
        在采购订单上增加付款状态跟踪功能：
        - 付款状态（未付/部分付款/已付/已开票）
        - 已付金额
        - 待付金额（自动计算）
        - 付款备注
    """,
    'author': 'PLS',
    'depends': ['purchase', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
