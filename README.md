# 家庭图书馆 (Family Library)

> 一家人都能用的私人藏书管理系统。一键 Docker 部署，自动从豆B拉评分和封面。

![License](https://img.shields.io/badge/license-MIT-green)
![Vue 3](https://img.shields.io/badge/frontend-Vue%203-42b883)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688)
![Docker](https://img.shields.io/badge/deploy-Docker%20Compose-2496ed)

## ✨ 特性

- 📖 **扫码/ISBN 录入**：输入 ISBN 自动从豆B拉取评分、封面、简介
- 🌟 **豆B同步**：HTML 爬虫（不依赖任何 API key），评分、标签、封面一键同步
- 📚 **分类 + 位置管理**：多维度分类 + 实物存放位置追踪
- 👨‍👩‍👧 **家庭共享**：多用户独立账号，独立记录阅读进度与借阅
- 📊 **阅读统计**：时长、习惯、分类分布可视化
- 🎨 **温润书香 UI**：古铜金 + 暖纸色 + 衬线大标题，远离 AI SaaS 灰
- 🐳 **Docker 一键部署**：compose 编排，SQLite + 上传文件全部持久化

## 📸 截图

> TODO: 加几张截图（书架页 + 详情抽屉 + Stats 统计页）

## 🏗 技术栈

| 层 | 选型 |
|---|---|
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Axios |
| 后端 | FastAPI + SQLAlchemy (async) + Pydantic v2 |
| 数据库 | SQLite (aiosqlite) |
| 数据源 | 豆B图书（HTML 爬虫，无需 key） |
| 部署 | Docker + Docker Compose + Nginx |
| 鉴权 | JWT (python-jose) + bcrypt |

## 🚀 快速开始

### 准备

- Docker + Docker Compose（macOS 推荐 [OrbStack](https://orbstack.dev)，Linux 推荐 Docker CE，飞牛 NAS 自带 Docker）

### 部署

**方式一：拉 GHCR 镜像（推荐，不需要源码）**

```bash
# 1. 在 NAS 上创建目录
mkdir -p /vol1/1000/docker/family-library/data/uploads

# 2. 下载 compose 文件
cd /vol1/1000/docker/family-library
curl -O https://raw.githubusercontent.com/vipuncle2026/family-library/main/docker-compose.ghcr.yml

# 3. 一键启动
docker compose -f docker-compose.ghcr.yml up -d

# 4. 打开浏览器
# http://<NAS-IP>:8180
```

**方式二：从源码构建（适合开发）**

```bash
# 1. 克隆
git clone https://github.com/vipuncle2026/family-library.git
cd family-library

# 2. 复制环境变量 (可选, 用默认也能跑)
cp .env.example .env

# 3. 一键启动
docker compose up -d --build

# 4. 打开浏览器
# http://localhost:8180
```

**默认管理员**：`admin` / `admin123`  
**⚠️ 部署成功后请立即改密码！** （登录后 → 家庭成员 → 编辑）

### 升级

```bash
# 方式一 (GHCR 镜像):
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d

# 方式二 (源码构建):
git pull
docker compose up -d --build
```

数据持久化在 `./data/` 目录，升级不丢。

### 重置

```bash
docker compose down -v
rm -rf data/library.db data/uploads/*
docker compose up -d --build    # 会重新 seed 演示数据
```

## 📁 目录结构

```
family-library/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/             # 路由 (books, auth, household, ...)
│   │   ├── core/            # 配置 / 数据库 / 安全
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic schema
│   │   ├── services/        # 豆B爬虫 + 缓存
│   │   └── main.py
│   ├── scripts/seed.py      # 演示数据初始化
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/           # Library / Records / Stats / Family / About / Login
│   │   ├── components/      # AddBookDialog / BookDetail / Topbar
│   │   ├── stores/          # Pinia
│   │   ├── api/             # Axios 封装
│   │   └── router/
│   ├── package.json
│   ├── vite.config.js
│   ├── nginx.conf           # 反代到后端 /api + /uploads
│   └── Dockerfile           # 两阶段: node build → nginx serve
├── data/                     # 运行时数据 (已 .gitignore)
│   ├── library.db
│   └── uploads/
├── docker-compose.yml        # 一键起后端 + 前端
├── DEPLOY.md                 # 飞牛 NAS 等详细部署文档
├── .env.example
├── LICENSE                   # MIT
└── README.md
```

## ⚙️ 配置说明

所有配置走环境变量，详见 [`.env.example`](.env.example)：

| 变量 | 含义 | 默认 |
|---|---|---|
| `PORT` | 前端容器对外暴露的主机端口 | `8180` |
| `DATABASE_URL` | SQLite 连接串 | `./data/library.db` |
| `SECRET_KEY` | JWT 签名密钥（**生产必改**） | 占位 |
| `UPLOAD_DIR` | 用户上传封面目录 | `./data/uploads` |
| `MAX_UPLOAD_SIZE` | 单文件上限 (字节) | `5242880` (5MB) |
| `META_TIMEOUT_SECONDS` | 豆B抓取超时 | `10` |
| `CORS_ORIGINS` | 允许的跨域源 | `["*"]` |

## 🔍 豆B数据源说明

豆B官方 API 自 2019 年起不再开放新 key。本项目**不依赖任何第三方 API key**，直接用 `httpx` 爬 `book.douban.com` 的公开页面提取评分、封面、标签。

**稳定性策略**：
- 本地 `meta_cache` 表按 ISBN 缓存 7 天（命中 < 50ms）
- 失败也写负缓存（避免反复打豆B被限流）
- 抓不到时引导用户手动录入

## 💾 备份与恢复

```bash
# 备份 (整个数据目录)
cp -r data/ data.bak.$(date +%Y%m%d)

# 恢复
cp -r data.bak.20260630/* data/
```

或用 git 管理 `data/library.db`（自行决定是否入仓）。

## 🛠 开发

```bash
# 后端 (单独跑, 不用 docker)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed          # 初始化演示数据
uvicorn app.main:app --reload --port 8000

# 前端 (单独跑)
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

## 🤝 贡献

欢迎 PR！提交前：

1. 后端：`pip install -r requirements.txt` 后跑一遍 `python -m scripts.seed && uvicorn app.main:app` 确认能起
2. 前端：`npm install && npm run build` 必须能 build 过
3. 别提交 `data/`、`.env`、`node_modules/`、`.workbuddy/`（已 ignore）
4. 单个 PR 聚焦一个改动，别夹带

详细：[CONTRIBUTING.md](CONTRIBUTING.md)

## 📋 后续规划

- [ ] 真正的摄像头扫码（浏览器 BarcodeDetector）
- [ ] Open Library / Google Books 备选数据源
- [ ] 管理员邀请码机制
- [ ] 借阅管理（谁借了哪本，何时还）
- [ ] 微信扫码登录（需要开放平台资质）

## 📄 协议

[MIT](LICENSE) © 2026 vipuncle2026
