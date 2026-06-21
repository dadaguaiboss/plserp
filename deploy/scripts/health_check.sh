#!/bin/bash
# ============================================
# 普洛狮ERP 健康检查脚本
# 使用方法: bash health_check.sh
# 定时任务: */5 * * * * /opt/prolion-erp/scripts/health_check.sh
# ============================================

set -uo pipefail

ODOO_URL="http://localhost:31013/web/health"
LOG_FILE="/opt/prolion-erp/logs/health.log"
SERVICE_NAME="prolion-erp"
MAX_RETRIES=2
RETRY_WAIT=15

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_health() {
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$ODOO_URL" 2>/dev/null)
    echo "$HTTP_CODE"
}

# 主检查逻辑
HTTP_CODE=$(check_health)

if [ "$HTTP_CODE" = "200" ]; then
    # 每小时记录一次正常日志，避免日志过大
    MINUTE=$(date +%M)
    if [ "$MINUTE" = "00" ]; then
        log_msg "[OK] 健康检查通过 (HTTP 200)"
    fi
    exit 0
fi

# 健康检查失败
log_msg "[WARN] 健康检查失败 (HTTP $HTTP_CODE)"

# 检查服务是否在运行
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    log_msg "[ERROR] 服务未运行，尝试启动..."
    sudo systemctl start "$SERVICE_NAME"
    sleep "$RETRY_WAIT"
else
    log_msg "[WARN] 服务运行中但无响应，尝试重启..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep "$RETRY_WAIT"
fi

# 重试检查
for i in $(seq 1 $MAX_RETRIES); do
    HTTP_CODE=$(check_health)
    if [ "$HTTP_CODE" = "200" ]; then
        log_msg "[OK] 重启后恢复正常 (尝试 $i/$MAX_RETRIES)"
        exit 0
    fi
    log_msg "[WARN] 重试 $i/$MAX_RETRIES 失败 (HTTP $HTTP_CODE)"
    sleep "$RETRY_WAIT"
done

log_msg "[CRITICAL] 多次重试后仍然失败，请人工检查！"
exit 1
