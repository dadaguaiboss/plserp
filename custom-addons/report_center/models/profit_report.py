from odoo import models, fields, tools


class ReportProfitAnalysis(models.Model):
    _name = 'report.profit.analysis'
    _description = '利润报表'
    _auto = False
    _order = 'period desc'

    product_id = fields.Many2one(
        'product.product',
        string='商品',
        readonly=True,
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='品牌',
        readonly=True,
    )
    platform = fields.Char(
        string='平台',
        readonly=True,
    )
    period = fields.Date(
        string='期间',
        readonly=True,
    )
    revenue = fields.Float(
        string='收入',
        readonly=True,
    )
    cost = fields.Float(
        string='成本',
        readonly=True,
    )
    gross_profit = fields.Float(
        string='毛利',
        readonly=True,
    )
    margin_rate = fields.Float(
        string='毛利率(%)',
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    sol.product_id AS product_id,
                    pt.brand_id AS brand_id,
                    so.warehouse_id::text AS platform,
                    DATE_TRUNC('month', so.date_order)::date AS period,
                    SUM(sol.price_subtotal) AS revenue,
                    SUM(sol.product_uom_qty * sol.purchase_price) AS cost,
                    SUM(sol.price_subtotal) - SUM(sol.product_uom_qty * COALESCE(sol.purchase_price, 0)) AS gross_profit,
                    CASE
                        WHEN SUM(sol.price_subtotal) > 0
                        THEN (SUM(sol.price_subtotal) - SUM(sol.product_uom_qty * COALESCE(sol.purchase_price, 0))) / SUM(sol.price_subtotal) * 100
                        ELSE 0
                    END AS margin_rate
                FROM sale_order_line sol
                LEFT JOIN sale_order so ON so.id = sol.order_id
                LEFT JOIN product_product pp ON pp.id = sol.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE so.state IN ('sale', 'done')
                GROUP BY sol.product_id, pt.brand_id, so.warehouse_id, DATE_TRUNC('month', so.date_order)
            )
        """ % self._table)
