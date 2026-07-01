# 飞牛 NAS / Linux NAS 部署说明

## 一键部署

```bash
# 1. 把整个 family-library 目录上传到 NAS
#    推荐位置: /vol1/1000/docker/family-library
#    (用飞牛的文件管理 / SMB / scp 都行)

# 2. SSH 进 NAS
ssh user@nas-ip
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

`docker-compose.yml` 已经把 `./data` 挂到容器 `/app/data`：

```
/vol1/1000/docker/family-library/
├── data/
│   ├── library.db          # SQLite 数据库
│   └── uploads/            # 用户上传的封面
├── docker-compose.yml
├── backend/
└── frontend/
```

- 升级代码：`docker compose up -d --build`，数据不丢
- 完全重置：`docker compose down -v` + 删 `./data` 目录

## 改端口

编辑 `docker-compose.yml`：

```yaml
ports:
  - "80:80"     # 改这里, 前面是 NAS 端口, 后面是容器内端口
```

## 走 HTTPS（推荐）

飞牛 NAS 一般有反向代理面板（`fnOS 反向代理` / `Caddy` / `NPM`），加一层即可。  
如果用本机 nginx，参考 `docker-compose.yml` 加 `nginx-proxy-manager` 服务。

## 镜像源说明

`Dockerfile` 已经用 `python:3.11-slim` / `nginx:alpine` / `node:20-alpine` 官方源，**国内网络也能拉**。

如果拉不动，手动加 registry mirror：

```bash
# 飞牛 Docker 设置 → 镜像加速 → 加 https://docker.m.daocloud.io
```

## 常见问题

**Q: 启动后访问 8180 空白？**  
A: 等 1 分钟让前端 build 完成，看 `docker compose logs -f frontend`。

**Q: 上传封面失败？**  
A: 检查 `./data/uploads` 目录权限 `chmod 777 data/uploads`。

**Q: SQLite 锁表 / 卡顿？**  
A: NAS 机械盘 + 网络存储 + SQLite 写入频繁会有这个问题。本项目家庭使用写入量小，应该没事。真出问题把 `data` 目录放到 SSD 卷。
