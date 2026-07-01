# 飞牛 NAS / Linux NAS 部署说明

## 方式一：拉 GHCR 镜像（推荐，不需要源码）

```bash
# 1. SSH 进 NAS, 创建目录
ssh user@nas-ip
mkdir -p /vol1/1000/docker/family-library/data/uploads
cd /vol1/1000/docker/family-library

# 2. 下载 compose 文件
curl -O https://raw.githubusercontent.com/vipuncle2026/family-library/main/docker-compose.ghcr.yml

# 3. 一键启动
docker compose -f docker-compose.ghcr.yml up -d

# 4. 浏览器打开
#    http://<NAS-IP>:8180
```

镜像已由 GitHub Actions 自动构建并推送到 GHCR，拉下来直接跑，无需本地 build。

### 升级

```bash
docker compose -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.ghcr.yml up -d
```

## 方式二：从源码构建

```bash
# 1. 把整个 family-library 目录上传到 NAS
#    推荐位置: /vol1/1000/docker/family-library
#    (用飞牛的文件管理 / SMB / scp 都行)

# 2. SSH 进 NAS
cd /vol1/1000/docker/family-library

# 3. 启动
docker compose up -d --build

# 4. 浏览器打开
#    http://<NAS-IP>:8180
```

首次启动会花 2-3 分钟构建（npm install + pip install + 前端 build），之后秒起。

## 管理员登录

- 账号: `admin`
- 密码: `admin123`

**⚠️ 部署成功后立刻改密码！** （登录后右上角 → 家庭成员 → 编辑）

## 数据持久化

compose 文件已经把 `./data` 挂到容器 `/app/data`：

```
/vol1/1000/docker/family-library/
├── data/
│   ├── library.db          # SQLite 数据库
│   └── uploads/            # 用户上传的封面
└── docker-compose.ghcr.yml (或 docker-compose.yml + 源码)
```

- 升级代码：pull + up -d，数据不丢
- 完全重置：`docker compose down -v` + 删 `./data` 目录

## 改端口

编辑 compose 文件：

```yaml
ports:
  - "8180:80"     # 改冒号前面, 后面 80 是容器内端口不要改
```

## 走 HTTPS（推荐）

飞牛 NAS 一般有反向代理面板（`fnOS 反向代理` / `Caddy` / `NPM`），加一层即可。
如果用本机 nginx，参考 compose 文件加 `nginx-proxy-manager` 服务。

## 镜像源说明

- **方式一 (GHCR)**：镜像从 `ghcr.io` 拉，国内可能需要加速。如果拉不动：
  ```bash
  # 飞牛 Docker 设置 → 镜像加速 → 加 https://ghcr.nju.edu.cn (南京大学 GHCR 镜像)
  ```
- **方式二 (源码构建)**：Dockerfile 用官方 `python:3.11-slim` / `nginx:alpine` / `node:20-alpine`，国内一般能拉。拉不动时：
  ```bash
  # 飞牛 Docker 设置 → 镜像加速 → 加 https://docker.m.daocloud.io
  ```

## GHCR 镜像可见性

GitHub Actions 构建的镜像默认是 **private**（即使仓库是 public）。

要让别人也能拉镜像：
1. 打开 https://github.com/vipuncle2026?tab=packages
2. 点进 `family-library-backend` 和 `family-library-frontend`
3. Package settings → Danger Zone → Change visibility → **Public**

## 常见问题

**Q: 启动后访问 8180 空白？**
A: 等 1 分钟让 seed 完成，看 `docker compose logs -f backend`。

**Q: 上传封面失败？**
A: 检查 `./data/uploads` 目录权限 `chmod 777 data/uploads`。

**Q: GHCR 镜像拉不动？**
A: 用南京大学镜像站 `ghcr.nju.edu.cn`，或者改用方式二从源码构建。

**Q: SQLite 锁表 / 卡顿？**
A: NAS 机械盘 + 网络存储 + SQLite 写入频繁会有这个问题。本项目家庭使用写入量小，应该没事。真出问题把 `data` 目录放到 SSD 卷。
