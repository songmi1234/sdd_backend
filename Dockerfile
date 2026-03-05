# 构建阶段：使用官方镜像，安装 UV 并构建依赖
FROM python:3.13-slim AS builder

WORKDIR /app

# 安装 UV（使用 pip + 清华源，避免直接复制镜像的兼容性问题）
RUN pip install --no-cache-dir uv -i https://mirrors.aliyun.com/pypi/simple/

# 复制依赖文件（优先复制锁文件，利用缓存）
COPY pyproject.toml uv.lock* ./

# 安装依赖（修复语法错误，移除多余分号；添加编译依赖安装）
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     g++ \
#     make \
#     && rm -rf /var/lib/apt/lists/* \
#     && uv venv /app/.venv \
#     && . /app/.venv/bin/activate \
#     && uv sync --frozen --no-install-project --index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN rm -f uv.lock \
    # 创建虚拟环境
    && uv venv /app/.venv \
    && . /app/.venv/bin/activate \
    # 同步依赖：强制使用阿里云源，不使用 frozen（避免锁文件）
    && uv sync --no-install-project --index-url https://mirrors.aliyun.com/pypi/simple/
# 运行阶段：精简镜像，仅复制必要文件
# 运行阶段：复制虚拟环境到 /venv
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv  

# 优化时区
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && echo ${TZ} > /etc/timezone && dpkg-reconfigure --frontend noninteractive tzdata && rm -rf /var/lib/apt/lists/*


# 1. 安装 Node.js 运行环境
# --no-install-recommends 保持镜像精简，rm -rf 清理缓存减少层大小
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     nodejs \
#     && rm -rf /var/lib/apt/lists/*
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    nodejs \
    && rm -rf /var/lib/apt/lists/*
COPY . .
# 把 /venv/bin 加入 PATH
# ENV PATH="/venv/bin:$PATH"
ENV PATH="/app/.venv/bin:$PATH"
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]