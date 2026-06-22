{
    'name': '普洛狮ERP基础模块',
    'version': '19.0.1.0.0',
    'category': 'Hidden',
    'summary': '普洛狮ERP品牌定制与基础配置',
    'description': """
普洛狮ERP (PLS ERP) 品牌定制模块
=====================================

本模块实现以下定制:
- 系统名称替换为"普洛狮ERP"
- 自定义登录页面样式
- 自定义系统 Logo 和 Favicon
- Web 客户端标题和页脚定制
- 初始化公司信息和系统参数
    """,
    'author': '普洛狮科技',
    'website': 'https://www.pls-erp.com',
    'depends': ['web', 'base', 'mail', 'base_setup'],
    'data': [
        'views/webclient_templates.xml',
        'views/login_templates.xml',
        'data/pls_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pls_base/static/src/css/pls_style.css',
            'pls_base/static/src/js/pls.js',
        ],
        'web.assets_frontend': [
            'pls_base/static/src/css/pls_login.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'sequence': 1,
}
