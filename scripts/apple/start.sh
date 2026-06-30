#!/usr/bin/env bash
# =============================================================================
# Apple Container 启动脚本 - 家庭图书馆
# 适用: macOS 26+ / Apple Silicon / apple/container 1.0+
# 用法:
#   ./scripts/apple/start.sh        # 后台启动 (默认)
#   ./scripts/apple/start.sh -f     # 前台启动 (看实时日志)
# =============================================================================

set -e

# 切到项目根目录
cd "$(dirname "$0")/../.."
ROOT="$(pwd)"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}!${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

# ---------- 0. 体检 ----------
log "检查环境..."

if ! command -v container >/dev/null 2>&1; then
  err "未找到 container 命令，请先安装 Apple Container"
  err "https://github.com/apple/container/releases"
  exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
  err "Apple Container 仅支持 Apple Silicon (arm64)"
  exit 1
fi

# 1.0+ 才稳
VERSION=$(container --version 2>/dev/null | grep -oE '1\.[0-9]+\.[0-9]+' | head -1 || echo "0.0.0")
MAJOR=$(echo "$VERSION" | cut -d. -f1)
if [[ "$MAJOR" -lt 1 ]]; then
  warn "当前 container 版本: $VERSION (< 1.0)，API 可能变动，建议升级"
fi

# ---------- 1. 启动系统服务 ----------
log "启动 container 系统服务..."
container system start >/dev/null 2>&1 || true
sleep 1

# ---------- 2. 加载 .env ----------
if [[ -f .env ]]; then
  set -a; source .env; set +a
  ok "已加载 .env"
else
  warn "未找到 .env，使用 .env.example 默认值"
  cp -n .env.example .env 2>/dev/null || true
  set -a; source .env.example; set +a
fi

DATA_DIR="$ROOT/data"
mkdir -p "$DATA_DIR"

# ---------- 3. 构建镜像 ----------
log "构建后端镜像 family-library-backend ..."
container build -t family-library-backend -f backend/Dockerfile backend/ 2>&1 | tail -3

log "构建前端镜像 family-library-frontend ..."
container build -t family-library-frontend -f frontend/Dockerfile frontend/ 2>&1 | tail -3

# ---------- 4. 清理旧容器 ----------
log "清理同名旧容器..."
container rm -f family-library-backend 2>/dev/null || true
container rm -f family-library-frontend 2>/dev/null || true

# ---------- 5. 启动后端 ----------
# Apple container 1.0 由 launchd 托管, --restart 不支持
# 通过 launchctl 加载服务实现开机自启
log "启动后端 (端口 8000)..."
container run -d \
  --name family-library-backend \
  -p 8000:8000 \
  -v "$DATA_DIR":/app/data \
  -e DATABASE_URL="sqlite:////app/data/library.db" \
  -e JWT_SECRET="${JWT_SECRET:-change-me-in-prod}" \
  -e DOUBAN_API_KEYS="${DOUBAN_API_KEYS:-}" \
  family-library-backend
ok "后端已启动"

# ---------- 6. 启动前端 ----------
log "启动前端 (端口 8080)..."
container run -d \
  --name family-library-frontend \
  -p 8080:80 \
  family-library-frontend
ok "前端已启动"

# ---------- 7. 等健康检查 ----------
log "等待服务就绪..."
for i in {1..15}; do
  if curl -fs http://localhost:8000/api/health >/dev/null 2>&1; then
    ok "后端健康检查通过"
    break
  fi
  sleep 1
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  家庭图书馆 启动成功${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  前端: ${BLUE}http://localhost:8080${NC}"
echo -e "  后端: ${BLUE}http://localhost:8000${NC}"
echo -e "  API 文档: ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  默认账户: ${YELLOW}admin / admin123${NC}"
echo ""
echo -e "  查看日志: ${YELLOW}container logs -f family-library-backend${NC}"
echo -e "  停止服务: ${YELLOW}./scripts/apple/stop.sh${NC}"
echo -e "${GREEN}========================================${NC}"
