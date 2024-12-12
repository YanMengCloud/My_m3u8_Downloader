# 使用官方 Python 镜像
FROM python:3.10-slim-buster

# 安装 FFmpeg 和 curl
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 配置 pip 使用阿里云源以加快包安装速度
COPY requirements.txt .
RUN pip install -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录并设置权限
RUN mkdir -p /app/temp /app/uploads && \
    chmod -R 755 /app

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

EXPOSE 3000

# 使用 python 直接运行，而不是通过 CMD
ENTRYPOINT ["python", "-u", "app.py"] 