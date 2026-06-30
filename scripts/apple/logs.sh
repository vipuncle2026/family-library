#!/usr/bin/env bash
# 查看家庭图书馆日志
# 用法: ./scripts/apple/logs.sh [backend|frontend]
TARGET="${1:-backend}"

case "$TARGET" in
  backend|be)  container logs -f family-library-backend ;;
  frontend|fe) container logs -f family-library-frontend ;;
  *) echo "用法: $0 [backend|frontend]"; exit 1 ;;
esac
