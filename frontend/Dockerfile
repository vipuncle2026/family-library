# ===== 一阶段构建前端 =====
# 用 node 镜像把 Vue 项目构建出 dist/
# 飞牛 NAS 跑时这一阶段会重复执行 (重新 build), 但 .dockerignore 已忽略 node_modules
FROM node:20-alpine AS frontend-build

WORKDIR /web

# 改用国内源, 飞牛/家用 NAS 拉 npm 包更稳
RUN npm config set registry https://registry.npmmirror.com

COPY package*.json ./
RUN npm install --no-audit --no-fund

COPY . .
RUN npm run build

# ===== 二阶段: 跑 nginx =====
# 不再依赖外部 dist, 把产物烤进镜像
FROM nginx:alpine

# 删掉 nginx 默认配置
RUN rm -f /etc/nginx/conf.d/default.conf

# 拷贝构建好的前端
COPY --from=frontend-build /web/dist /usr/share/nginx/html

# 拷贝我们写的 nginx 配置 (反代 /api 和 /uploads 到 backend 服务)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# nginx 镜像默认 CMD 已含, 不需要再写
