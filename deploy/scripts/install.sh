#!/bin/bash
# ============================================
# 普洛狮ERP 一键安装脚本
# 适用于 Ubuntu 22.04/24.04 LTS
# 使用方法: sudo bash install.sh
# ============================================

set -euo pipefail

echo "============================================"
echo " 普洛狮ERP (ProLion ERP) 一键安装"
echo " 基于 Odoo 19 Community Edition"
echo "============================================"
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] 请使用 sudo 运行此脚本"
    exit 1
fi

# === 配置变量 ===
PROLION_USER="prolion"
PROLION_HOME="/opt/prolion-erp"
PYTHON_VERSION="3.12"
DB_HOST="58.250.155.28"
DB_PORT="31002"

echo "[1/8] 更新系统包..."
apt update && apt upgrade -y

echo "[2/8] 安装系统依赖..."
apt install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev \
    build-essential git curl wget \
    libxml2-dev libxslt1-dev zlib1g-dev \
    libsasl2-dev libldap2-dev libssl-dev libffi-dev \
    libjpeg-dev libpq-dev liblcms2-dev \
    libfreetype6-dev libharfbuzz-dev libfribidi-dev \
    wkhtmltopdf xfonts-75dpi xfonts-base \
    fonts-noto-cjk fonts-wqy-zenhei \
    nginx postgresql-client \
    supervisor logrotate

echo "[3/8] 创建系统用户..."
if ! id "$PROLION_USER" &>/dev/null; then
    useradd -m -d "$PROLION_HOME" -U -r -s /bin/bash "$PROLION_USER"
    echo "  用户 $PROLION_USER 已创建"
else
    echo "  用户 $PROLION_USER 已存在，跳过"
fi

echo "[4/8] 创建目录结构..."
mkdir -p "$PROLION_HOME"/{server,custom-addons,data,logs,backups,scripts}

echo "[5/8] 检查源代码..."
if [ ! -f "$PROLION_HOME/server/odoo-bin" ]; then
    echo "  [提示] 请将 Odoo 19 源代码上传到 $PROLION_HOME/server/"
    echo "  可以使用以下方式之一:"
    echo "    方式1: scp -r D:\\plserp\\* user@server:$PROLION_HOME/server/"
    echo "    方式2: 通过宝塔面板文件管理器上传"
    echo "    方式3: git clone --depth 1 -b 19.0 https://github.com/odoo/odoo.git $PROLION_HOME/server/"
    echo ""
    echo "  上传完成后，请重新运行此脚本。"
    echo "  如果代码已在其他位置，按 Enter 继续..."
    read -p ""
fi

echo "[6/8] 创建 Python 虚拟环境并安装依赖..."
if [ ! -d "$PROLION_HOME/venv" ]; then
    sudo -u "$PROLION_USER" python${PYTHON_VERSION} -m venv "$PROLION_HOME/venv"
fi

if [ -f "$PROLION_HOME/server/requirements.txt" ]; then
    sudo -u "$PROLION_USER" "$PROLION_HOME/venv/bin/pip" install --upgrade pip wheel
    sudo -u "$PROLION_USER" "$PROLION_HOME/venv/bin/pip" install -r "$PROLION_HOME/server/requirements.txt"
    echo "  Python 依赖安装完成"
else
    echo "  [警告] 未找到 requirements.txt，跳过依赖安装"
fi

echo "[7/8] 安装配置文件..."

# 复制配置文件（如果不存在）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -f "$PROLION_HOME/prolion-erp.conf" ]; then
    if [ -f "$SCRIPT_DIR/../prolion-erp.conf" ]; then
        cp "$SCRIPT_DIR/../prolion-erp.conf" "$PROLION_HOME/prolion-erp.conf"
    else
        echo "  [警告] 未找到配置文件模板，请手动创建 $PROLION_HOME/prolion-erp.conf"
    fi
fi
chmod 640 "$PROLION_HOME/prolion-erp.conf" 2>/dev/null || true

# 复制运维脚本
cp "$SCRIPT_DIR/backup.sh" "$PROLION_HOME/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/health_check.sh" "$PROLION_HOME/scripts/" 2>/dev/null || true
cp "$SCRIPT_DIR/restore.sh" "$PROLION_HOME/scripts/" 2>/dev/null || true
chmod +x "$PROLION_HOME/scripts/"*.sh 2>/dev/null || true

# 安装 systemd 服务
if [ -f "$SCRIPT_DIR/../systemd/prolion-erp.service" ]; then
    cp "$SCRIPT_DIR/../systemd/prolion-erp.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable prolion-erp
    echo "  systemd 服务已安装并设为开机启动"
fi

# 安装 Nginx 配置
if [ -f "$SCRIPT_DIR/../nginx/prolion-erp.conf" ]; then
    # 替换 upstream 为本地地址（非 Docker 模式）
    sed 's/prolion-erp:31011/127.0.0.1:31011/g; s/prolion-erp:31012/127.0.0.1:31012/g' \
        "$SCRIPT_DIR/../nginx/prolion-erp.conf" > /etc/nginx/sites-available/prolion-erp
    ln -sf /etc/nginx/sites-available/prolion-erp /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
    echo "  Nginx 反向代理已配置"
fi

# 安装 logrotate 配置
cat > /etc/logrotate.d/prolion-erp << 'LOGROTATE_EOF'
/opt/prolion-erp/logs/prolion-erp.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
LOGROTATE_EOF

# 设置所有权
chown -R "$PROLION_USER:$PROLION_USER" "$PROLION_HOME"

echo "[8/8] 设置定时任务..."

# 备份定时任务（每日凌晨2点）
(crontab -u "$PROLION_USER" -l 2>/dev/null || true; \
 echo "0 2 * * * $PROLION_HOME/scripts/backup.sh >> $PROLION_HOME/logs/backup.log 2>&1") \
 | sort -u | crontab -u "$PROLION_USER" -

# 健康检查定时任务（每5分钟）
(crontab -u root -l 2>/dev/null || true; \
 echo "*/5 * * * * $PROLION_HOME/scripts/health_check.sh") \
 | sort -u | crontab -u root -

echo ""
echo "============================================"
echo " 安装完成！"
echo "============================================"
echo ""
echo " 后续步骤:"
echo ""
echo " 1. 确保源代码已在 $PROLION_HOME/server/"
echo ""
echo " 2. 修改配置文件中的数据库密码:"
echo "    vi $PROLION_HOME/prolion-erp.conf"
echo ""
echo " 3. 确保 PostgreSQL 数据库已就绪:"
echo "    psql -h $DB_HOST -p $DB_PORT -U prolion -d prolion_erp"
echo ""
echo " 4. 初始化数据库:"
echo "    sudo su - $PROLION_USER"
echo "    source $PROLION_HOME/venv/bin/activate"
echo "    python $PROLION_HOME/server/odoo-bin \\"
echo "        -c $PROLION_HOME/prolion-erp.conf \\"
echo "        -d prolion_erp \\"
echo "        -i base,web,contacts,sale,purchase,stock,account,l10n_cn \\"
echo "        --load-language=zh_CN \\"
echo "        --stop-after-init"
echo ""
echo " 5. 启动服务:"
echo "    sudo systemctl start prolion-erp"
echo ""
echo " 6. 访问系统:"
echo "    http://服务器IP:31013"
echo "    默认管理员: admin / admin"
echo ""
echo "============================================"
