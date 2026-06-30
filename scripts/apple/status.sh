#!/usr/bin/env bash
# 查看家庭图书馆状态
echo "=== 容器状态 ==="
container ls --format "table {{.ID}}\t{{.Names}}\t{{.State}}\t{{.Ports}}" 2>/dev/null \
  | grep -E "family-library|NAMES" || echo "(无)"

echo ""
echo "=== 后端健康检查 ==="
if curl -fs http://localhost:8000/api/health 2>/dev/null; then
  echo " ← OK"
else
  echo "  ✗ 后端未响应"
fi

echo ""
echo "=== 前端健康检查 ==="
if curl -fsI http://localhost:8080 2>/dev/null | head -1; then
  echo " ← OK"
else
  echo "  ✗ 前端未响应"
fi
