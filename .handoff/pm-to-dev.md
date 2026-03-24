# Task: Sprint 4 — Polish, Testing & Deployment

Priority: P0 | Status: PENDING

## Context
Sprint 1-3 全部完成。后端 AI 管线 + 前端升级都已就位。最后一个 Sprint：打磨、测试、确保可部署。

## Task 1: 端到端测试 & Bug 修复

启动前后端，完整测试两个模式：

**后端启动：**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**前端启动：**
```bash
cd frontend
npm install
npm run dev
```

**测试清单：**
- [ ] AI 模式：上传图片 → 三视图预览 → 选动作 → 生成精灵表 → 预览动画 → 下载 PNG → 下载 GIF
- [ ] Classic 模式：上传图片 → 选动作 → 生成 → 下载
- [ ] 模式切换：在 AI 和 Classic 之间切换，状态正确重置
- [ ] 错误处理：上传非图片文件、超大文件、无效格式
- [ ] "Create Another" 重置流程正常
- [ ] 移动端布局（缩小浏览器窗口测试）
- [ ] API 返回错误时前端显示友好信息

修复发现的所有 bug。

## Task 2: 三视图缓存

实现三视图缓存机制，同一张图片不同动作复用三视图：

**后端 `backend/app/services/ai_pipeline/turnaround.py`：**
- 用图片内容的 hash (md5/sha256) 作为缓存 key
- 三视图保存到 `static/turnarounds/{hash}/` 目录
- 生成前检查缓存，命中则直接返回
- 新增端点或参数：`turnaround_id` 可传入 generate 跳过重复生成

**前端：**
- 如果用户选了不同动作但没换图片，复用已有的三视图（不重新调 turnaround API）
- 在 App.tsx 中用 state 记住 turnaround 结果

## Task 3: Docker Compose 更新

更新 `docker-compose.yml` 使整个项目可一键启动：

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/static:/app/static
    environment:
      - AI_PROVIDER=mock  # 默认 mock 模式

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

- 移除 torchserve 服务（不再是核心依赖）
- 确保 Dockerfile 都能正常 build
- 测试 `docker-compose up` 能跑通

## Task 4: README 更新

重写 `README.md` 反映新架构：
- 项目介绍（AI-first sprite sheet 生成）
- 两种模式说明（AI HD / Classic）
- 快速开始（本地开发 + Docker）
- API 文档概要
- 架构图（简单 ASCII）
- 技术栈
- 移除过时的 Azure 部署内容（不是当前重点）

## Task 5: 代码清理

- 移除未使用的 import
- 统一日志格式（用 logger 不用 print）
- 确保所有 async 函数正确使用 await
- `requirements.txt` 检查：移除不需要的依赖，确认版本
- `package.json` 检查：确认依赖都用到了
- 前端 `npm run build` + `npm run lint` 无报错
- 后端 typing 检查（基本的 type hint）

## Acceptance Criteria
- [ ] 两种模式端到端全流程无 bug
- [ ] 三视图缓存生效（同图不同动作不重复生成）
- [ ] `docker-compose up` 能正常启动
- [ ] README 准确反映当前项目状态
- [ ] 代码无明显 lint 问题
- [ ] `npm run build` 无报错
- [ ] `uvicorn app.main:app` 启动无报错
- [ ] 最终提交推送到 GitHub
