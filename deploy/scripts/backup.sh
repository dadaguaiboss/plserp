#!/bin/bash
# ============================================
# 普洛狮ERP 自动备份脚本
# 使用方法: bash backup.sh
# 定时任务: 0 2 * * * /opt/prolion-erp/scripts/backup.sh >> /opt/prolion-erp/logs/backup.log 2>&1
# ============================================

set -euo pipefail

# === 配置 ===
BACKUP_DIR="/opt/prolion-erp/backups"
DB_HOST="58.250.155.28"
DB_PORT="31002"
DB_USER="prolion"
DB_NAME="prolion_erp"
DATA_DIR="/opt/prolion-erp/data"
CONFIG_FILE="/opt/prolion-erp/prolion-erp.conf"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

# === 颜色输出 ===
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"
}

# === 开始备份 ===
log_info "=== 普洛狮ERP 备份开始 ==="

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 1. 数据库备份（自定义格式，支持选择性恢复）
log_info "正在备份数据库..."
if PGPASSWORD="${PGPASSWORD:-}" pg_dump \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    -Fc "$DB_NAME" > "$BACKUP_DIR/db_${DB_NAME}_${DATE}.dump"; then
    DB_SIZE=$(du -sh "$BACKUP_DIR/db_${DB_NAME}_${DATE}.dump" | cut -f1)
    log_info "数据库备份完成 (大小: $DB_SIZE)"
else
    log_error "数据库备份失败！"
fi

# 2. 文件存储备份（附件、图片等）
if [ -d "$DATA_DIR/filestore" ]; then
    log_info "正在备份文件存储..."
    tar czf "$BACKUP_DIR/filestore_${DATE}.tar.gz" -C "$DATA_DIR" filestore/ 2>/dev/null
    FS_SIZE=$(du -sh "$BACKUP_DIR/filestore_${DATE}.tar.gz" | cut -f1)
    log_info "文件存储备份完成 (大小: $FS_SIZE)"
else
    log_info "文件存储目录不存在，跳过"
fi

# 3. 配置文件备份
if [ -f "$CONFIG_FILE" ]; then
    cp "$CONFIG_FILE" "$BACKUP_DIR/config_${DATE}.conf"
    log_info "配置文件备份完成"
fi

# 4. 清理旧备份
DELETED_COUNT=$(find "$BACKUP_DIR" \( -name "*.dump" -o -name "*.tar.gz" -o -name "*.conf" \) -mtime +$KEEP_DAYS -print -delete | wc -l)
log_info "已清理 $DELETED_COUNT 个超过 ${KEEP_DAYS} 天的旧备份文件"

# 5. 显示当前备份占用空间
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/*.dump 2>/dev/null | wc -l)
log_info "备份目录总大小: $TOTAL_SIZE, 数据库备份数量: $BACKUP_COUNT"

log_info "=== 普洛狮ERP 备份完成 ==="
