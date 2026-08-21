# =====================================================
# 保险精准营销系统 · Docker 镜像
# 构建：docker compose build    启动：docker compose up -d
#
# 基础镜像（Docker Hub 被墙时，请在 Docker 的 registry-mirrors 配置国内加速源，
# 见 docker-compose.yml 顶部注释）
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

# 换清华 apt 源（Debian 官方源国内不可达，trixie 套件清华镜像可用）
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true

# 中文字体（防图表乱码）+ OpenMP 运行时库（xgboost/scikit-learn 依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-noto-cjk \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖（利用 Docker 层缓存，代码变更不重复下载）
# 默认用清华 PyPI 镜像加速，可换回官方：docker compose build --build-arg PIP_INDEX=https://pypi.org/simple
ARG PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i ${PIP_INDEX}

# 拷贝源码（.env 已被 .dockerignore 排除，密钥由 compose 环境变量注入）
COPY . .

# 运行时目录（数据卷挂载点，配合 compose volumes）
RUN mkdir -p /app/data/models /app/data/visualizations /app/instance

EXPOSE 5000

# 健康检查：容器启动后探测首页
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/', timeout=3)"

CMD ["python", "run_flask.py"]
