{
    'name': '售后管理',
    'version': '19.0.1.0.0',
    'category': 'Sales/After Sales',
    'summary': '平台售后申请管理、自动审核规则引擎、仓库核验',
    'description': """
售后管理模块
============

功能特性:
- 平台售后申请自动同步
- 规则引擎自动审核（7天无理由、质量问题、高价值单等）
- 丽迅仓库核验流程
- 审核结果自动上传平台
- 退货/换货/退款/补发全流程管理
    """,
    'author': '普洛狮科技',
    'website': 'https://www.pls-erp.com',
    'depends': ['sale', 'stock', 'product', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/aftersale_rule_data.xml',
        'views/aftersale_order_views.xml',
        'views/aftersale_rule_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
