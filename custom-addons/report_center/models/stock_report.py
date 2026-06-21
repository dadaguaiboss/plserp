from odoo import models, fields, tools


class ReportStockSummary(models.Model):
    _name = 'report.stock.summary'
    _description = '库存报表'
    _auto = False
    _order = 'product_id'

    product_id = fields.Many2one(
        'product.product',
        string='商品',
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='仓库',
        readonly=True,
    )
    brand_id = fields.Many2one(
        'product.brand',
        string='品牌',
        readonly=True,
    )
    qty_on_hand = fields.Float(
        string='在手库存',
        readonly=True,
    )
    qty_in_transit = fields.Float(
        string='在途库存',
        readonly=True,
    )
    qty_in_channel = fields.Float(
        string='渠道库存',
        readonly=True,
    )
    qty_reserved = fields.Float(
        string='预留库存',
        readonly=True,
    )
    qty_available = fields.Float(
        string='可用库存',
        readonly=True,
    )
    stock_value = fields.Float(
        string='库存金额',
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    sq.product_id AS product_id,
                    sw.id AS warehouse_id,
                    pt.brand_id AS brand_id,
                    COALESCE(SUM(sq.quantity), 0) AS qty_on_hand,
                    0 AS qty_in_transit,
                    0 AS qty_in_channel,
                    COALESCE(SUM(sq.reserved_quantity), 0) AS qty_reserved,
                    COALESCE(SUM(sq.quantity - sq.reserved_quantity), 0) AS qty_available,
                    COALESCE(SUM(sq.quantity * pt.list_price), 0) AS stock_value
                FROM stock_quant sq
                LEFT JOIN stock_location sl ON sl.id = sq.location_id
                LEFT JOIN stock_warehouse sw ON sw.lot_stock_id = sl.id
                LEFT JOIN product_product pp ON pp.id = sq.product_id
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE sl.usage = 'internal'
                GROUP BY sq.product_id, sw.id, pt.brand_id
            )
        """ % self._table)
