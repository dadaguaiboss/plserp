#!/bin/bash
# ============================================
# 普洛狮ERP 模块管理工具
# 使用方法: bash module_manager.sh [install|update|scaffold] [模块名]
# ============================================

set -euo pipefail

PROLION_HOME="/opt/prolion-erp"
VENV="$PROLION_HOME/venv/bin/python"
ODOO_BIN="$PROLION_HOME/server/odoo-bin"
CONFIG="$PROLION_HOME/prolion-erp.conf"
DB_NAME="prolion_erp"

show_help() {
    echo "普洛狮ERP 模块管理工具"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  install <模块名>    安装模块"
    echo "  update <模块名>     更新模块"
    echo "  updateall           更新所有模块（谨慎使用）"
    echo "  scaffold <模块名>   创建新模块骨架"
    echo "  list                列出自定义模块"
    echo ""
    echo "示例:"
    echo "  $0 install prolion_base"
    echo "  $0 update prolion_cn"
    echo "  $0 scaffold my_new_module"
}

case "${1:-help}" in
    install)
        MODULE="${2:?请指定模块名}"
        echo "正在安装模块: $MODULE ..."
        $VENV $ODOO_BIN -c $CONFIG -d $DB_NAME -i "$MODULE" --stop-after-init
        echo "安装完成"
        ;;
    update)
        MODULE="${2:?请指定模块名}"
        echo "正在更新模块: $MODULE ..."
        $VENV $ODOO_BIN -c $CONFIG -d $DB_NAME -u "$MODULE" --stop-after-init
        echo "更新完成"
        ;;
    updateall)
        echo "警告: 即将更新所有模块，这可能需要较长时间。"
        read -p "确认继续? (yes/no): " CONFIRM
        if [ "$CONFIRM" = "yes" ]; then
            $VENV $ODOO_BIN -c $CONFIG -d $DB_NAME -u all --stop-after-init
            echo "更新完成"
        fi
        ;;
    scaffold)
        MODULE="${2:?请指定模块名}"
        $VENV $ODOO_BIN scaffold "$MODULE" "$PROLION_HOME/custom-addons/"
        echo "模块骨架已创建: $PROLION_HOME/custom-addons/$MODULE"
        ;;
    list)
        echo "自定义模块列表:"
        ls -1 "$PROLION_HOME/custom-addons/" 2>/dev/null || echo "  (无自定义模块)"
        ;;
    *)
        show_help
        ;;
esac
