# Spritify - Product Requirements Document (v2)

## Vision
Upload a static character image → AI generates turnaround views → generates animated sprite sheet with consistent character appearance.

## Core Innovation
**三视图驱动的角色一致性** — 不是骨骼变形，而是 AI 理解角色后从多角度重新生成。

## MVP Scope (Revised)

### Must Have
1. **Upload image** — PNG/JPG/WebP, drag & drop
2. **AI 三视图生成** — 自动生成正面/侧面/背面
3. **三视图预览** — 用户确认角色生成质量
4. **Select motion** — walk, run, idle, jump (4 核心动作)
5. **AI 动作帧生成** — ControlNet + IP-Adapter，基于三视图保持一致
6. **Sprite sheet 合成 + 预览 + 下载**

### Should Have
- Classic mode (AnimatedDrawings) 作为快速/免费 fallback
- GIF 下载选项
- 三视图缓存（同角色多动作复用）

### Out of Scope
- 用户账户
- 自定义动作上传
- 批量生成
- 自部署 AI 模型（全走 API）

## User Flow (Revised)
```
上传图片 → [AI 生成三视图] → 预览/确认三视图 → 选择动作 → [AI 生成动作帧] → 预览动画 → 下载 Sprite Sheet
```

## Architecture
See `DECISIONS.md` (ADR-001 v2) for full technical design.

**Key:** AI-first pipeline via Replicate API. AnimatedDrawings is optional fallback.

## Sprint Plan
1. Sprint 1: AI Pipeline Core — 三视图生成 + Replicate 集成
2. Sprint 2: Pose-Conditioned 帧生成
3. Sprint 3: Frontend 升级
4. Sprint 4: 打磨 + 部署
