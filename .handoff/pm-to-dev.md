# Task: Sprint 3 — Frontend Upgrade

Priority: P0 | Status: PENDING

## Context
Sprint 1 (AI 管线骨架) 和 Sprint 2 (动作帧生成) 后端都已完成。现在升级前端，匹配新的 AI-first 流程。

## 新用户流程
```
上传图片 → [AI 生成三视图] → 预览三视图 → 选择动作 → [AI 生成动作帧] → 预览精灵表 → 下载
```

## Task 1: 新增三视图预览步骤

新增组件 `frontend/src/components/TurnaroundPreview.tsx`:
- 上传图片后，自动调用 `POST /api/v1/turnaround` 
- 展示 3 张视图（正面/侧面/背面）并排显示
- "确认" 按钮进入下一步；"重新生成" 按钮可重试
- Loading 状态 + 错误处理

修改 `App.tsx` 流程:
```
Step 1: Upload → Step 2: Turnaround Preview (NEW) → Step 3: Select Motion → Step 4: Settings → Generate
```

## Task 2: 模式切换 UI

新增组件 `frontend/src/components/ModeSelector.tsx`:
- 两个模式卡片: "AI HD" 和 "Classic"
- AI HD: "高质量，AI 生成多视角，保证角色一致性" + ⚡ 标记
- Classic: "快速模式，骨骼变形动画" + 🚀 标记
- 放在上传之前或之后都行，看你觉得哪个 UX 更好

API 层修改 `frontend/src/api/index.ts`:
- `generateSprite()` 新增 `mode` 参数
- 新增 `generateTurnaround(image: File)` 函数
- 新增 `TurnaroundResult` 类型

## Task 3: 多步骤进度条

重构 `GenerationProgress.tsx`:
- AI 模式下显示多步骤进度:
  - Step 1/3: 生成三视图... (10-30%)
  - Step 2/3: 生成动作帧... (30-80%)
  - Step 3/3: 合成精灵表... (80-100%)
- Classic 模式保持原有单步进度
- 每个步骤有小图标或文字标记

## Task 4: GIF 下载选项

修改结果展示区域:
- 下载按钮改为两个: "下载 PNG Sprite Sheet" + "下载 GIF 动画"
- GIF 下载需要后端新增端点（或者前端用 canvas 生成 GIF — 用 gif.js 库）
- 如果后端做：新增 `GET /api/v1/download/{task_id}?format=gif`
- 如果前端做：用现有 sprite sheet + canvas 合成 GIF

**推荐前端做** — 用 `gif.js` 或类似库，省一次 API 调用：
```bash
cd frontend && npm install gif.js
```

## Task 5: UI 打磨

- 页面标题区域加 logo/icon（可以用 emoji 🎮 或简单 SVG）
- 上传区域：如果是 AI 模式，提示 "上传角色正面图效果最佳"
- 动画预览：加播放速度控制（慢/正常/快）
- 响应式布局检查（移动端能用）

## 技术要求
- 保持 React 19 + TypeScript + TailwindCSS
- 不引入新的状态管理库（useState/useEffect 够用）
- 组件拆分合理，不要把所有逻辑塞在 App.tsx

## Acceptance Criteria
- [ ] AI 模式：上传 → 三视图预览 → 选动作 → 生成 → 下载，全流程走通
- [ ] Classic 模式：上传 → 选动作 → 生成 → 下载，保持原有流程
- [ ] 模式切换 UI 直观
- [ ] 多步骤进度条反映真实状态
- [ ] PNG + GIF 两种下载格式
- [ ] 移动端可用
- [ ] `npm run build` 无报错
