{
    'name': '无头件管理',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': '无头件（无法匹配订单的退货包裹）管理、自动匹配、批量导入',
    'description': """
无头件管理模块
==============

功能特性:
- 丽迅无头件批量导入
- 自动匹配算法（物流单号精确匹配、手机号模糊匹配、SKU匹配）
- 匹配置信度分级（高→自动关联，中→人工确认，未匹配→待处理）
- 超90天未匹配自动清理
- 关联售后单创建
    """,
    'author': '普洛狮科技',
    'website': 'https://www.pls-erp.com',
    'depends': ['stock', 'sale', 'mail', 'aftersale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'wizard/headless_import_wizard_views.xml',
        'views/headless_package_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
