# Spritify — Architecture Decision Record

## ADR-001: AI-First Multi-View Sprite Generation (Revised)

**Date:** 2026-03-24  
**Status:** APPROVED  
**Revision:** v2 — Director 明确要求以 AI 三视图为核心，AD 降级为可选 fallback

---

## Core Requirement
从单张角色图片生成三视图（正面/侧面/背面），基于三视图生成动作帧，确保角色外观在所有帧中一致。

## Constraint
- 无 GPU (Intel Xeon, 8GB RAM) — 所有 AI 推理必须走外部 API
- 需要一个可靠的 API 服务（Replicate / Stability AI / Fal.ai）

---

## Architecture: AI-First Pipeline

```
用户上传图片
    │
    ▼
┌─────────────────────────┐
│  Stage 1: 三视图生成     │
│  Single Image → Front,  │
│  Side, Back views       │
│  (Zero123++ / SV3D /    │
│   CharTurner / Era3D)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Stage 2: 动作帧生成     │
│  For each frame:        │
│  - Select best view     │
│    angle as reference   │
│  - ControlNet + OpenPose│
│    for target pose      │
│  - IP-Adapter for       │
│    character consistency │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Stage 3: 精灵表合成     │
│  - Background removal   │
│  - Uniform sizing       │
│  - Grid composition     │
│  - PNG output           │
└─────────────────────────┘
```

## Stage 1: 三视图生成 — 技术选型

### 方案 1A: Zero123++ (Replicate)
- **原理**: 扩散模型，从单视角生成多视角一致图像
- **输入**: 单张图片
- **输出**: 6 个视角（可选 front/side/back）
- **API**: `replicate.run("stability-ai/zero123plus")`
- **成本**: ~$0.03/run
- **速度**: ~10-15s
- **适用**: 3D 风格角色、实物照片
- **局限**: 对纯 2D 平面画风（像素画、简笔画）效果一般

### 方案 1B: Era3D / Wonder3D (Replicate)  
- **原理**: 专为多视图生成设计的模型
- **输入**: 单张图片 + 目标角度
- **输出**: 指定角度的渲染图
- **API**: `replicate.run("pengHTYX/era3d")`
- **成本**: ~$0.05/run
- **速度**: ~20s
- **适用**: 各种画风
- **局限**: 速度较慢

### 方案 1C: SDXL + CharTurner LoRA (Replicate/Fal.ai)
- **原理**: SDXL 基础模型 + 角色转身专用 LoRA
- **输入**: 原图 + prompt 描述 + 目标角度
- **输出**: 指定角度的角色图
- **API**: Fal.ai SDXL 或 Replicate SDXL
- **成本**: ~$0.02/image
- **速度**: ~5s
- **适用**: 卡通/动漫/插画风格 ← **Spritify 核心场景**
- **局限**: 需要精心 prompt engineering，一致性靠 IP-Adapter 保证

### 方案 1D: Stable Diffusion + ControlNet Multi-View
- **原理**: SD + MV ControlNet 条件生成
- **输入**: 原图 + depth/normal map
- **输出**: 多视角图
- **适用**: 一般

### 推荐
- **主要目标用户是卡通/游戏角色** → 先用 **1C (SDXL + CharTurner)** 做 MVP
- 同时支持 **1A (Zero123++)** 作为 3D 风格角色的备选
- 两个模型都在 Replicate 上有现成 API，切换成本低

## Stage 2: 动作帧生成 — 技术选型

### 方案 2A: ControlNet + OpenPose + IP-Adapter
- **流程**:
  1. 预定义每个动作的 OpenPose 骨骼序列（走/跑/跳/待机 等）
  2. 选择与当前帧角度最匹配的三视图作为参考
  3. ControlNet(OpenPose) 控制姿势 + IP-Adapter 保持角色外观
  4. 生成每一帧
- **API**: Replicate SDXL + ControlNet + IP-Adapter
- **成本**: ~$0.02-0.03/frame
- **速度**: ~3-5s/frame
- **质量**: 高，角色一致性好

### 方案 2B: AnimateDiff / SVD
- **原理**: 视频生成模型，直接生成动作视频
- **输入**: 角色图 + 运动描述
- **输出**: 短视频 → 抽帧
- **API**: Replicate SVD
- **成本**: ~$0.05/video
- **速度**: ~15s
- **质量**: 中等，帧间一致但动作控制不精确
- **局限**: 难以精确控制每帧姿势

### 推荐
- **2A (ControlNet + OpenPose + IP-Adapter)** — 帧级精确控制，适合 sprite sheet
- 2B 可作为 "快速预览" 模式

## Stage 3: 精灵表合成
复用现有 `SpriteSheetService` — 已经能做帧合成、缩放、网格排列。小改即可。

---

## New Backend Architecture

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── generation.py      # 主生成 API（重构）
│   │   └── turnaround.py      # NEW: 三视图 API
│   ├── services/
│   │   ├── ai_pipeline.py     # NEW: AI 生成管线（核心）
│   │   │   ├── turnaround.py  # 三视图生成
│   │   │   ├── pose_frames.py # 动作帧生成
│   │   │   └── providers/     # API 提供商适配
│   │   │       ├── replicate.py
│   │   │       └── fal.py
│   │   ├── animator.py        # 保留: AD 经典模式
│   │   ├── sprite_sheet.py    # 保留: 精灵表合成
│   │   └── pose_library.py    # NEW: OpenPose 预置骨骼库
│   └── models/
│       └── schemas.py         # Pydantic models
├── pose_data/                  # NEW: 预置 OpenPose JSON
│   ├── walk/
│   ├── run/
│   ├── idle/
│   └── jump/
└── requirements.txt
```

## New API Design

### POST /api/v1/generate (重构)
```json
{
  "mode": "ai",           // "ai" (default) | "classic" (AnimatedDrawings)
  "motion_id": "walk",
  "frame_count": 8,
  "frame_size": 128,
  "style": "cartoon"      // hint for AI generation
}
+ image file (multipart)
```

### POST /api/v1/turnaround (新增)
```json
// 单独生成三视图（可选步骤，也可以在 generate 中自动做）
+ image file (multipart)

Response:
{
  "turnaround_id": "xxx",
  "views": {
    "front": "/static/turnarounds/xxx_front.png",
    "side": "/static/turnarounds/xxx_side.png",
    "back": "/static/turnarounds/xxx_back.png"
  }
}
```

### GET /api/v1/motions (保留)
新增字段: `pose_data` (OpenPose JSON 预览)

---

## Revised Sprint Plan

### Sprint 1: AI Pipeline Core (重新定义)
**不再是修 AD bug，而是搭建 AI 管线骨架**

Tasks:
1. 集成 Replicate Python SDK
2. 实现三视图生成服务 (Zero123++ 和/或 SDXL+CharTurner)
3. 实现 `/api/v1/turnaround` 端点
4. 测试三视图生成质量
5. 保留 AD 管线作为 `mode=classic` fallback（顺便修之前发现的 bug）

### Sprint 2: Pose-Conditioned Frame Generation
1. 创建 OpenPose 预置骨骼库（walk/run/idle/jump 各 8 帧）
2. 实现 ControlNet + IP-Adapter 帧生成服务
3. 实现完整 generate 端点（三视图 → 动作帧 → 精灵表）
4. 端到端测试

### Sprint 3: Frontend Upgrade
1. 新增三视图预览步骤
2. "AI HD" vs "Classic" 模式切换
3. 生成进度实时更新（多步骤进度）
4. 下载选项（PNG/GIF）

### Sprint 4: Polish
1. 缓存三视图（同角色不同动作复用）
2. 用量追踪和限制
3. 错误恢复和重试
4. Docker 部署更新

---

## Cost Model (Per Sprite Sheet — AI Mode)
| Step | API Calls | Cost |
|------|----------|------|
| 三视图生成 | 1 call | $0.03-0.05 |
| 动作帧生成 (8帧) | 8 calls | $0.16-0.24 |
| **Total** | | **$0.19-0.29** |

缓存三视图后，同角色第二个动作只需 $0.16-0.24。
