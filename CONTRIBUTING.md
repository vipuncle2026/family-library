# 🤝 贡献指南

感谢你愿意贡献代码或文档！

## 提 PR 前必做

1. **后端自检**：
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m compileall -q app scripts
   uvicorn app.main:app --reload  # 确认能起
   ```

2. **前端自检**：
   ```bash
   cd frontend
   npm install
   npm run build                    # 必须能 build 过
   ```

3. **不要提交**：
   - `data/`、`backend/data/`、`.env`、`node_modules/`、`.workbuddy/`、`dist/`、`diagnose/`、`outputs/`
   - 这些已在 `.gitignore`，加新的大文件/临时产物时记得加 ignore

## 提交规范

- 一个 PR 一个主题，别夹带
- commit message 简短，例如：
  - `fix: 评分徽章空星加描边`
  - `feat: 添加借阅管理`
  - `docs: 修正 README 密码`
  - `chore: 升级 fastapi 到 0.116`

## 提 issue

- bug 用 `.github/ISSUE_TEMPLATE/bug.md`
- 功能用 `.github/ISSUE_TEMPLATE/feature.md`
- 问问题直接 issue，标题加 `[question]`

## 分支约定

- `main` — 稳定分支，GHCR 镜像从这打
- `feat/xxx` / `fix/xxx` — 功能/修复分支，提 PR 到 main

## 部署兼容性

提交代码时考虑：
- SQLite 默认配置能跑（不要硬编码 PostgreSQL）
- 默认 5MB 上传限制不要随意改大
- 不要把任何 API key 写进代码（豆瓣走 HTML 爬虫）

欢迎任何 PR！小到 typo 也行 😎
