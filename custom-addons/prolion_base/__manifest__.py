{
    'name': '普洛狮ERP基础模块',
    'version': '19.0.1.0.0',
    'category': 'Hidden',
    'summary': '普洛狮ERP品牌定制与基础配置',
    'description': """
普洛狮ERP (ProLion ERP) 品牌定制模块
=====================================

本模块实现以下定制:
- 系统名称替换为"普洛狮ERP"
- 自定义登录页面样式
- 自定义系统 Logo 和 Favicon
- Web 客户端标题和页脚定制
- 初始化公司信息和系统参数
    """,
    'author': '普洛狮科技',
    'website': 'https://www.prolion-erp.com',
    'depends': ['web', 'base', 'mail', 'base_setup'],
    'data': [
        'views/webclient_templates.xml',
        'views/login_templates.xml',
        'data/prolion_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'prolion_base/static/src/css/prolion_style.css',
            'prolion_base/static/src/js/prolion.js',
        ],
        'web.assets_frontend': [
            'prolion_base/static/src/css/prolion_login.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
    'sequence': 1,
}
