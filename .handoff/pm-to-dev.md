# Task: Sprint 1 — AI Pipeline Core (架构重定义)

Priority: P0 | Status: PENDING  
**⚠️ 替代之前的 "Fix Backend Issues" 任务 — 方向已改**

## Context
Director 明确要求：AI 三视图生成是核心，不是修 AnimatedDrawings 的 bug。整个架构方向变了。

**新目标：** 搭建 AI-first 生成管线，用 Replicate API 从单张图片生成角色三视图。

## 前置条件
- 需要 **Replicate API Token** — 等 Director 提供，先把代码架构搭好，用 mock 测试
- 如果有 token 就直接联调

## Task 1: 搭建 AI 管线骨架

### 1.1 安装依赖
`backend/requirements.txt` 新增:
```
replicate>=0.25.0
```

### 1.2 创建 AI Pipeline Service
创建 `backend/app/services/ai_pipeline/` 目录:

**`__init__.py`**

**`turnaround.py`** — 三视图生成服务:
```python
class TurnaroundService:
    async def generate_views(self, image_path: str) -> dict:
        """
        从单张图片生成三视图 (front, side, back)
        
        Returns: {
            "front": "/path/to/front.png",
            "side": "/path/to/side.png", 
            "back": "/path/to/back.png"
        }
        """
        # 调用 Replicate API
        # 模型选项:
        #   1. stability-ai/zero123plus (3D 风格)
        #   2. SDXL + CharTurner LoRA (卡通风格)
        # 
        # 先实现 Zero123++ 作为默认
        pass
```

**`providers/replicate_provider.py`** — Replicate API 封装:
```python
class ReplicateProvider:
    def __init__(self, api_token: str):
        self.client = replicate.Client(api_token=api_token)
    
    async def run_zero123plus(self, image_path: str) -> list[str]:
        """运行 Zero123++ 模型，返回多视角图片 URL 列表"""
        pass
    
    async def run_sdxl_turnaround(self, image_path: str, prompt: str) -> list[str]:
        """运行 SDXL + CharTurner，返回三视图 URL 列表"""
        pass
```

### 1.3 新增 API 端点
**`backend/app/api/turnaround.py`** (新文件):
```
POST /api/v1/turnaround
- 接收图片上传
- 调用 TurnaroundService
- 返回三视图 URL
- 保存三视图到 static/turnarounds/
```

### 1.4 配置更新
**`backend/app/config.py`** 新增:
```python
replicate_api_token: Optional[str] = None  # env: REPLICATE_API_TOKEN
ai_provider: str = "replicate"             # or "mock" for testing
```

### 1.5 Mock 模式
在没有 API token 时，`TurnaroundService` 应该有 mock 模式:
- 复制原图 3 次，加不同的颜色 overlay 标记 (front=绿, side=蓝, back=红)
- 这样前端和 API 层可以先跑通

## Task 2: 重构 Generation API

修改 `backend/app/api/generation.py`:
- 新增 `mode` 参数: `"ai"` (default) | `"classic"`
- `mode=ai`: 调用新 AI 管线
- `mode=classic`: 调用现有 AnimatedDrawings（顺便修之前说的 bug）
- AI 模式暂时只做到三视图（帧生成是 Sprint 2）

## Task 3: 顺便修 AD 的关键 Bug

在 `mode=classic` 路径中:
- 修 `jumping_jacks` retarget 配置路径
- 加 `asyncio.to_thread()` 包裹阻塞调用
- 加基础输入验证

这些是小改动，顺手做了。

## 目录结构 (目标)
```
backend/app/services/
├── ai_pipeline/
│   ├── __init__.py
│   ├── turnaround.py          # 三视图生成
│   ├── pose_frames.py         # Sprint 2 — 先留空
│   └── providers/
│       ├── __init__.py
│       ├── replicate_provider.py
│       └── mock_provider.py   # 无 API key 时的 mock
├── animator.py                # 保留 (classic mode)
├── sprite_sheet.py            # 保留
├── pose_detector.py           # 保留
└── storage.py                 # 保留
```

## Acceptance Criteria
- [ ] `POST /api/v1/turnaround` 能接收图片，返回三视图（mock 或真实）
- [ ] `POST /api/v1/generate` 支持 `mode=ai` 和 `mode=classic`
- [ ] Mock 模式下全流程可跑通（无 API key）
- [ ] 有 Replicate token 时能调通 Zero123++
- [ ] AD 经典模式的 3 个关键 bug 已修
- [ ] 代码结构清晰，新旧管线分离
- [ ] `uvicorn app.main:app` 启动无报错

## 参考
- Replicate Zero123++ API: https://replicate.com/stability-ai/zero123plus
- Replicate Python SDK: https://github.com/replicate/replicate-python
- 完整架构设计: `.handoff/DECISIONS.md`
