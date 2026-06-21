# ============================================
# Dockerfile - 普洛狮ERP (ProLion ERP)
# 基于 Odoo 19 Community Edition
# ============================================
FROM python:3.12-slim-bookworm

LABEL maintainer="普洛狮科技"
LABEL description="ProLion ERP based on Odoo 19"
LABEL version="19.0.1.0"

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV ODOO_RC=/opt/prolion-erp/prolion-erp.conf

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libsasl2-dev \
    libldap2-dev \
    libssl-dev \
    libffi-dev \
    libjpeg62-turbo-dev \
    libpq-dev \
    liblcms2-dev \
    libfreetype6-dev \
    wkhtmltopdf \
    xfonts-75dpi \
    xfonts-base \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 创建运行用户
RUN useradd -m -d /opt/prolion-erp -U -r -s /bin/bash prolion

# 复制 Odoo 源代码
COPY --chown=prolion:prolion odoo/ /opt/prolion-erp/server/odoo/
COPY --chown=prolion:prolion addons/ /opt/prolion-erp/server/addons/
COPY --chown=prolion:prolion odoo-bin /opt/prolion-erp/server/odoo-bin
COPY --chown=prolion:prolion requirements.txt /opt/prolion-erp/server/requirements.txt
COPY --chown=prolion:prolion setup.py /opt/prolion-erp/server/setup.py
COPY --chown=prolion:prolion setup.cfg /opt/prolion-erp/server/setup.cfg

# 复制自定义模块
COPY --chown=prolion:prolion custom-addons/ /opt/prolion-erp/custom-addons/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r /opt/prolion-erp/server/requirements.txt

# 创建必要目录
RUN mkdir -p /opt/prolion-erp/{data,logs,backups} \
    && chown -R prolion:prolion /opt/prolion-erp

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:31011/web/health || exit 1

USER prolion
WORKDIR /opt/prolion-erp/server

EXPOSE 31011 31012

VOLUME ["/opt/prolion-erp/data", "/opt/prolion-erp/logs", "/opt/prolion-erp/custom-addons"]

ENTRYPOINT ["python", "odoo-bin"]
CMD ["-c", "/opt/prolion-erp/prolion-erp.conf"]
