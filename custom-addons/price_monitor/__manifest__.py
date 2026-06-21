{
    'name': '行情监测',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': '竞品价格监控与预警分析',
    'description': """
        行情监测模块：
        - 监控竞品平台价格
        - 价格波动预警
        - 价格趋势分析
    """,
    'author': 'Prolion',
    'depends': ['product', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/price_monitor_views.xml',
        'views/price_record_views.xml',
        'views/price_alert_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
