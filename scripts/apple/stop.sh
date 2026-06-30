#!/usr/bin/env bash
# 停止家庭图书馆服务
set -e
cd "$(dirname "$0")/../.."

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}停止服务...${NC}"
container stop family-library-backend  2>/dev/null && echo "  后端已停止" || echo "  后端未运行"
container stop family-library-frontend 2>/dev/null && echo "  前端已停止" || echo "  前端未运行"
container rm   family-library-backend  2>/dev/null || true
container rm   family-library-frontend 2>/dev/null || true
echo -e "${GREEN}✓ 已清理${NC}"
