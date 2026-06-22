{
    'name': '普洛狮ERP-中国本地化增强',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': '中国本地化增强：中文报表模板、公司信息扩展、税务适配',
    'description': """
普洛狮ERP 中国本地化增强模块
==============================

功能:
- 中文格式的发票/报价单/采购单报表模板
- 公司信息扩展（统一社会信用代码、开户银行信息）
- 人民币大写金额转换
- 中国地址格式适配
    """,
    'author': '普洛狮科技',
    'website': 'https://www.pls-erp.com',
    'depends': [
        'base',
        'account',
        'sale',
        'purchase',
        'stock',
        'l10n_cn',
        'pls_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'report/report_templates.xml',
        'data/pls_cn_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
