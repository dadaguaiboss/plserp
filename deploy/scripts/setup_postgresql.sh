#!/bin/bash
# ============================================
# 普洛狮ERP PostgreSQL 安装脚本
# 在数据库服务器上运行此脚本安装 PostgreSQL
# 适用于 Ubuntu/Debian 系统
# 使用方法: sudo bash setup_postgresql.sh
# ============================================

set -euo pipefail

PG_VERSION="16"
PG_PORT="31002"
DB_NAME="prolion_erp"
DB_USER="prolion"
# 请在运行前修改此密码！
DB_PASSWORD="CHANGE_ME_TO_YOUR_STRONG_PASSWORD"

echo "============================================"
echo " PostgreSQL ${PG_VERSION} 安装脚本"
echo " 端口: ${PG_PORT}"
echo " 数据库: ${DB_NAME}"
echo " 用户: ${DB_USER}"
echo "============================================"
echo ""

# 检查 root
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] 请使用 sudo 运行"
    exit 1
fi

# 检查操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "[ERROR] 无法检测操作系统"
    exit 1
fi

echo "[1/6] 安装 PostgreSQL ${PG_VERSION}..."

case "$OS" in
    ubuntu|debian)
        # 添加 PostgreSQL 官方源
        apt install -y curl ca-certificates gnupg
        curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" > /etc/apt/sources.list.d/pgdg.list
        apt update
        apt install -y postgresql-${PG_VERSION} postgresql-client-${PG_VERSION}
        ;;
    centos|rhel|rocky|almalinux)
        dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-$(rpm -E %{rhel})-x86_64/pgdg-redhat-repo-latest.noarch.rpm
        dnf install -y postgresql${PG_VERSION}-server postgresql${PG_VERSION}
        /usr/pgsql-${PG_VERSION}/bin/postgresql-${PG_VERSION}-setup initdb
        ;;
    *)
        echo "[ERROR] 不支持的操作系统: $OS"
        exit 1
        ;;
esac

echo "[2/6] 配置 PostgreSQL..."

# 确定配置文件路径
case "$OS" in
    ubuntu|debian)
        PG_CONF="/etc/postgresql/${PG_VERSION}/main/postgresql.conf"
        PG_HBA="/etc/postgresql/${PG_VERSION}/main/pg_hba.conf"
        PG_SERVICE="postgresql"
        ;;
    centos|rhel|rocky|almalinux)
        PG_CONF="/var/lib/pgsql/${PG_VERSION}/data/postgresql.conf"
        PG_HBA="/var/lib/pgsql/${PG_VERSION}/data/pg_hba.conf"
        PG_SERVICE="postgresql-${PG_VERSION}"
        ;;
esac

# 修改端口和监听地址
sed -i "s/#port = 5432/port = ${PG_PORT}/" "$PG_CONF"
sed -i "s/port = 5432/port = ${PG_PORT}/" "$PG_CONF"
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"

# 性能调优（8GB 内存基准）
cat >> "$PG_CONF" << PG_PERF_EOF

# === 普洛狮ERP 性能调优 ===
shared_buffers = 2GB
effective_cache_size = 6GB
work_mem = 64MB
maintenance_work_mem = 512MB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 512MB
max_connections = 200
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on
PG_PERF_EOF

echo "[3/6] 配置远程访问..."

# 添加远程访问规则
echo "# 普洛狮ERP 远程访问" >> "$PG_HBA"
echo "host    ${DB_NAME}    ${DB_USER}    0.0.0.0/0    scram-sha-256" >> "$PG_HBA"

echo "[4/6] 启动 PostgreSQL..."
systemctl enable "$PG_SERVICE"
systemctl restart "$PG_SERVICE"
sleep 3

echo "[5/6] 创建数据库和用户..."

sudo -u postgres psql -p "$PG_PORT" << PSQL_EOF
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER USER ${DB_USER} CREATEDB;
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER} ENCODING 'UTF8' TEMPLATE template0;
PSQL_EOF

echo "[6/6] 验证安装..."

# 验证连接
if sudo -u postgres psql -p "$PG_PORT" -c "SELECT version();" > /dev/null 2>&1; then
    echo ""
    echo "============================================"
    echo " PostgreSQL 安装成功！"
    echo "============================================"
    echo ""
    echo " 连接信息:"
    echo "   主机: $(hostname -I | awk '{print $1}')"
    echo "   端口: ${PG_PORT}"
    echo "   数据库: ${DB_NAME}"
    echo "   用户: ${DB_USER}"
    echo "   密码: (已设置)"
    echo ""
    echo " 测试连接:"
    echo "   psql -h $(hostname -I | awk '{print $1}') -p ${PG_PORT} -U ${DB_USER} -d ${DB_NAME}"
    echo ""
    echo " 如果有防火墙，请放行端口 ${PG_PORT}:"
    echo "   sudo ufw allow ${PG_PORT}/tcp"
    echo ""
else
    echo "[ERROR] PostgreSQL 安装可能存在问题，请检查日志"
fi
