# ReadEcho Pro Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# ============ 构建阶段 ============
FROM python:3.9-slim AS builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -e .

# ============ 运行阶段 ============
FROM python:3.9-slim AS runtime

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    # 音频处理依赖
    libportaudio2 \
    libsndfile1 \
    # FFmpeg (用于音频处理)
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置非root用户
RUN useradd -m -u 1000 readecho
USER readecho
WORKDIR /home/readecho

# 创建应用目录
RUN mkdir -p /home/readecho/.readecho/logs

# 复制应用代码
COPY --chown=readecho:readecho . /home/readecho/app

# 设置环境变量
ENV PYTHONPATH=/home/readecho/app
ENV PYTHONUNBUFFERED=1
ENV LOG_DIR=/home/readecho/.readecho/logs
ENV DATABASE_FILE=/home/readecho/.readecho/readecho.db

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 运行应用
CMD ["python", "-m", "main"]

# ============ 开发阶段 ============
FROM builder AS dev

# 安装开发依赖
RUN pip install -e ".[dev]"

# 设置开发环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 复制应用代码
COPY . /app

# 开发命令
CMD ["python", "-m", "pytest", "tests/", "-v"]