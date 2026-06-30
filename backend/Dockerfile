FROM python:3.11-slim

WORKDIR /app

# 装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖, 利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 数据 + 上传文件 持久化目录
VOLUME ["/app/data", "/app/data/uploads"]

EXPOSE 8000

# 启动: 先 seed 演示数据, 再起 uvicorn
CMD ["sh", "-c", "python -m scripts.seed || true; uvicorn app.main:app --host 0.0.0.0 --port 8000"]
