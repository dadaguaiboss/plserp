# Part of PLS ERP. See LICENSE file for full copyright and licensing details.

import base64
import io

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import xlrd
    HAS_XLRD = True
except ImportError:
    HAS_XLRD = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class HeadlessImportWizard(models.TransientModel):
    _name = 'headless.import.wizard'
    _description = '无头件批量导入向导'

    file = fields.Binary(string='导入文件', required=True)
    file_name = fields.Char(string='文件名')
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='仓库',
        required=True,
    )
    import_result = fields.Text(string='导入结果', readonly=True)

    def action_import(self):
        """执行批量导入"""
        self.ensure_one()

        if not self.file:
            raise UserError(_('请上传导入文件。'))

        file_content = base64.b64decode(self.file)
        file_name = self.file_name or ''

        if file_name.endswith('.xlsx'):
            rows = self._parse_xlsx(file_content)
        elif file_name.endswith('.xls'):
            rows = self._parse_xls(file_content)
        elif file_name.endswith('.csv'):
            rows = self._parse_csv(file_content)
        else:
            raise UserError(_('不支持的文件格式，请上传 .xlsx、.xls 或 .csv 文件。'))

        success_count = 0
        error_count = 0
        errors = []

        HeadlessPackage = self.env['headless.package']

        for idx, row in enumerate(rows, start=2):
            try:
                tracking_number = str(row.get('tracking_number', '') or '').strip()
                if not tracking_number:
                    errors.append(_('第 %d 行：物流单号不能为空') % idx)
                    error_count += 1
                    continue

                vals = {
                    'tracking_number': tracking_number,
                    'sender_name': str(row.get('sender_name', '') or '').strip(),
                    'sender_phone': str(row.get('sender_phone', '') or '').strip(),
                    'product_description': str(row.get('product_description', '') or '').strip(),
                    'qty': float(row.get('qty', 1) or 1),
                    'warehouse_id': self.warehouse_id.id,
                }

                receive_date = row.get('receive_date', '')
                if receive_date:
                    vals['receive_date'] = str(receive_date).strip()

                notes = row.get('notes', '')
                if notes:
                    vals['notes'] = str(notes).strip()

                HeadlessPackage.create(vals)
                success_count += 1

            except Exception as e:
                errors.append(_('第 %d 行导入失败: %s') % (idx, str(e)))
                error_count += 1

        result_msg = _('导入完成！成功: %d 条，失败: %d 条。') % (
            success_count, error_count
        )
        if errors:
            result_msg += '\n\n' + _('错误详情:\n') + '\n'.join(errors[:50])

        self.import_result = result_msg

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'headless.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _parse_xlsx(self, file_content):
        """解析 xlsx 文件"""
        if not HAS_OPENPYXL:
            raise UserError(_('缺少 openpyxl 库，请安装: pip install openpyxl'))

        wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True)
        ws = wb.active

        rows_iter = ws.iter_rows()
        header_row = next(rows_iter)
        headers = self._map_headers([
            cell.value for cell in header_row
        ])

        rows = []
        for row in rows_iter:
            values = [cell.value for cell in row]
            row_dict = dict(zip(headers, values))
            rows.append(row_dict)

        wb.close()
        return rows

    def _parse_xls(self, file_content):
        """解析 xls 文件"""
        if not HAS_XLRD:
            raise UserError(_('缺少 xlrd 库，请安装: pip install xlrd'))

        wb = xlrd.open_workbook(file_contents=file_content)
        ws = wb.sheet_by_index(0)

        header_values = [ws.cell_value(0, col) for col in range(ws.ncols)]
        headers = self._map_headers(header_values)

        rows = []
        for row_idx in range(1, ws.nrows):
            values = [ws.cell_value(row_idx, col) for col in range(ws.ncols)]
            row_dict = dict(zip(headers, values))
            rows.append(row_dict)

        return rows

    def _parse_csv(self, file_content):
        """解析 csv 文件"""
        import csv

        # 尝试不同编码
        for encoding in ('utf-8-sig', 'utf-8', 'gbk', 'gb2312'):
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise UserError(_('无法解析文件编码，请使用 UTF-8 编码。'))

        reader = csv.DictReader(io.StringIO(text))
        raw_headers = reader.fieldnames or []
        header_map = self._get_header_mapping()

        rows = []
        for raw_row in reader:
            row = {}
            for raw_key, value in raw_row.items():
                mapped_key = header_map.get(raw_key.strip(), raw_key.strip())
                row[mapped_key] = value
            rows.append(row)

        return rows

    def _map_headers(self, raw_headers):
        """将中文表头映射为内部字段名"""
        header_map = self._get_header_mapping()
        return [
            header_map.get(str(h or '').strip(), str(h or '').strip())
            for h in raw_headers
        ]

    def _get_header_mapping(self):
        """中文表头到字段名的映射"""
        return {
            '物流单号': 'tracking_number',
            '快递单号': 'tracking_number',
            '运单号': 'tracking_number',
            '寄件人': 'sender_name',
            '寄件人姓名': 'sender_name',
            '寄件人电话': 'sender_phone',
            '电话': 'sender_phone',
            '手机号': 'sender_phone',
            '商品描述': 'product_description',
            '商品': 'product_description',
            '描述': 'product_description',
            '数量': 'qty',
            '件数': 'qty',
            '收件日期': 'receive_date',
            '日期': 'receive_date',
            '到件日期': 'receive_date',
            '备注': 'notes',
        }
