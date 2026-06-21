#!/bin/bash
# ============================================
# 普洛狮ERP 数据库恢复脚本
# 使用方法: bash restore.sh <备份文件路径>
# 示例: bash restore.sh /opt/prolion-erp/backups/db_prolion_erp_20260621_020000.dump
# ============================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "用法: $0 <备份文件路径> [文件存储备份路径]"
    echo "示例: $0 /opt/prolion-erp/backups/db_prolion_erp_20260621.dump"
    echo "      $0 /opt/prolion-erp/backups/db_prolion_erp_20260621.dump /opt/prolion-erp/backups/filestore_20260621.tar.gz"
    exit 1
fi

DUMP_FILE="$1"
FILESTORE_ARCHIVE="${2:-}"
DB_HOST="58.250.155.28"
DB_PORT="31002"
DB_USER="prolion"
DB_NAME="prolion_erp"
DATA_DIR="/opt/prolion-erp/data"
SERVICE_NAME="prolion-erp"

if [ ! -f "$DUMP_FILE" ]; then
    echo "[ERROR] 备份文件不存在: $DUMP_FILE"
    exit 1
fi

echo "============================================"
echo " 普洛狮ERP 数据库恢复"
echo "============================================"
echo ""
echo "  备份文件:   $DUMP_FILE"
echo "  数据库:     $DB_NAME @ $DB_HOST:$DB_PORT"
echo ""
echo "  警告: 此操作将覆盖当前数据库中的所有数据！"
echo ""
read -p "确认恢复? (输入 yes 继续): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "[1/4] 停止普洛狮ERP服务..."
sudo systemctl stop "$SERVICE_NAME" || true
sleep 3

echo "[2/4] 恢复数据库..."
PGPASSWORD="${PGPASSWORD:-}" pg_restore \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -d "$DB_NAME" --clean --if-exists \
    "$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo "  数据库恢复成功"
else
    echo "  数据库恢复完成（可能有部分警告，通常可忽略）"
fi

echo "[3/4] 恢复文件存储..."
if [ -n "$FILESTORE_ARCHIVE" ] && [ -f "$FILESTORE_ARCHIVE" ]; then
    tar xzf "$FILESTORE_ARCHIVE" -C "$DATA_DIR/"
    echo "  文件存储恢复成功"
else
    echo "  跳过文件存储恢复（未提供备份文件）"
fi

echo "[4/4] 启动普洛狮ERP服务..."
sudo systemctl start "$SERVICE_NAME"
sleep 5

# 验证
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "============================================"
    echo " 恢复完成！服务已启动。"
    echo " 访问: http://localhost:31013"
    echo "============================================"
else
    echo ""
    echo "[ERROR] 服务启动失败，请检查日志:"
    echo "  tail -f /opt/prolion-erp/logs/prolion-erp.log"
fi
