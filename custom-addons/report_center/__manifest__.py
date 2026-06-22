{
    'name': '报表中心',
    'version': '19.0.1.0.0',
    'category': 'Reporting',
    'summary': '集中展示各类业务报表',
    'description': """
        报表中心模块：
        - 库存报表（库存总览、在途、渠道库存等）
        - 利润报表（收入、成本、毛利分析）
        - 集中式报表入口
    """,
    'author': 'PLS',
    'depends': ['base', 'purchase', 'sale', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_report_views.xml',
        'views/profit_report_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
