# OrbStack 一键启动指南

## 为什么用 OrbStack

Apple Container 1.0 在 macOS 27 早期 build 上 helper 注册有问题，OrbStack 跟 Docker Desktop 语法完全兼容、**比 Docker Desktop 轻量十倍**、对 Apple Silicon 原生支持，是这个项目最合适的运行时。

- 启动时间: 几秒
- 空闲 CPU: < 0.1%
- 磁盘占用: < 10MB
- 完美支持 `docker compose` 子命令
- 自带 `docker-compose.yml` 解析

## 步骤

### 1. 下载安装 OrbStack

```bash
brew install --cask orbstack
```

或者从官网下载: <https://orbstack.dev/download>

### 2. 启动 OrbStack

装完后第一次启动会初始化 Linux VM，等几十秒。

验证:

```bash
docker --version
docker compose version
docker ps
```

应该看到版本信息和空容器列表。

### 3. 拉起家庭图书馆

直接走原来的 docker-compose:

```bash
cd /Users/awei/Desktop/vibetest/temp10/family-library
docker compose up -d --build
```

### 4. 访问

- 前端: <http://localhost:8080>
- 后端 API: <http://localhost:8000>
- API 文档: <http://localhost:8000/docs>
- 默认账户: `admin / admin123`

### 5. 常用命令

```bash
# 看日志
docker compose logs -f

# 停服务
docker compose down

# 重启单个
docker compose restart backend

# 重建镜像
docker compose build --no-cache

# 进后端容器
docker compose exec backend bash

# 看资源占用
docker stats
```

## 与 Apple Container 共存

OrbStack 跟 Apple Container 端口不冲突。两者可以同时装（OrbStack 走自己的 Linux VM，Apple Container 走 macOS microVM），但 `docker` 命令的 PATH 会被 OrbStack 抢走——这是好事，OrbStack 的 `docker` CLI 体验跟 Docker Desktop 一模一样。

如果以后 Apple Container 1.x 修好了 helper 问题，想切回去:

```bash
# 临时用 Apple Container (不推荐现在用)
PATH=/usr/local/bin:$PATH container system start
PATH=/usr/local/bin:$PATH ./scripts/apple/start.sh
```

## 数据持久化

`./data/` 目录是 SQLite 数据库，备份就是 `cp -r data/ data.bak-$(date +%F)`。
