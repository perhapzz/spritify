# Task: Sprint 2 — Pose-Conditioned Frame Generation

Priority: P0 | Status: PENDING

## Context
Sprint 1 AI 管线骨架已完成（三视图生成服务 + Mock 模式）。现在搭建第二阶段：基于三视图 + OpenPose 生成动作帧。

Token 不 block 开发 — 继续用 Mock 模式，所有接口和逻辑先跑通。

## Task 1: OpenPose 预置骨骼库

创建 `backend/pose_data/` 目录，存放预定义的 OpenPose JSON：

```
pose_data/
├── walk/          # 8 帧步行循环
│   ├── frame_0.json
│   ├── frame_1.json
│   └── ...
├── run/           # 8 帧跑步循环
├── idle/          # 4 帧待机呼吸
└── jump/          # 8 帧跳跃
```

每个 JSON 是标准 OpenPose 18-keypoint 格式：
```json
{
  "people": [{
    "pose_keypoints_2d": [x0, y0, c0, x1, y1, c1, ...]
  }]
}
```

**获取方式：**
- 可以从网上找现成的 OpenPose 序列数据
- 或者手动定义关键帧坐标（走路/跑步这些动作模式很标准）
- 也可以从现有 BVH 文件投影出 2D 关键点

创建 `backend/app/services/pose_library.py`:
```python
class PoseLibrary:
    def get_pose_sequence(self, motion_id: str, frame_count: int) -> list[dict]:
        """返回指定动作的 OpenPose 关键点序列"""
        pass
    
    def list_motions(self) -> list[dict]:
        """列出所有可用动作"""
        pass
```

## Task 2: Pose-Conditioned Frame Generation Service

实现 `backend/app/services/ai_pipeline/pose_frames.py`:

```python
class PoseFrameService:
    async def generate_frames(
        self,
        turnaround_views: dict,  # {"front": path, "side": path, "back": path}
        motion_id: str,
        frame_count: int = 8,
        frame_size: int = 128,
    ) -> list[str]:
        """
        基于三视图 + OpenPose 生成动作帧
        
        流程:
        1. 从 PoseLibrary 获取目标动作的骨骼序列
        2. 对每一帧:
           a. 根据帧的朝向角度，选择最匹配的三视图作为参考
           b. 调用 ControlNet(OpenPose) + IP-Adapter 生成该帧
           c. 去除背景
        3. 返回帧图片路径列表
        """
        pass
```

**Replicate API 调用设计（在 replicate_provider.py 中新增）：**
```python
async def run_controlnet_pose(
    self,
    reference_image: str,    # 三视图中最匹配的那张
    pose_image: str,         # OpenPose 骨骼图
    prompt: str,             # 角色描述
    ip_adapter_scale: float = 0.7,
) -> str:
    """ControlNet + IP-Adapter 生成单帧"""
    pass
```

**Mock 模式（在 mock_provider.py 中新增）：**
- 对每帧：取三视图中的一张，根据 pose 做简单的色调/旋转变换
- 目的是让前端和 API 逻辑能完整跑通

## Task 3: 整合到 Generate 端点

修改 `backend/app/api/generation.py` 的 `mode=ai` 路径：

```
完整 AI 生成流程:
1. 上传图片 → 调用 TurnaroundService 生成三视图
2. 三视图 → 调用 PoseFrameService 生成动作帧
3. 动作帧 → 调用 SpriteSheetService 合成精灵表
4. 返回结果
```

进度更新要真实反映多步骤：
- 10%: 上传完成
- 30%: 三视图生成中
- 50%: 三视图完成，动作帧生成中
- 80%: 动作帧完成，合成精灵表
- 100%: 完成

## Task 4: OpenPose 骨骼渲染工具

创建 `backend/app/services/ai_pipeline/pose_renderer.py`:
```python
def render_pose_image(keypoints: list, width: int, height: int) -> Image:
    """将 OpenPose 关键点渲染为骨骼图（黑底白线）"""
    # 用 Pillow 画骨骼连线
    # 这个图作为 ControlNet 的条件输入
    pass
```

## Acceptance Criteria
- [ ] `pose_data/` 下有 walk/run/idle/jump 4 个动作的 OpenPose 序列
- [ ] `PoseLibrary` 能返回动作骨骼序列
- [ ] `PoseFrameService` 能基于三视图 + 骨骼生成帧（Mock 模式）
- [ ] `POST /api/v1/generate` (mode=ai) 能完整走通：三视图 → 动作帧 → 精灵表
- [ ] 进度更新反映真实多步骤状态
- [ ] Mock 模式下全流程端到端可跑通
- [ ] Replicate provider 中新增 `run_controlnet_pose` 方法（真实调用待 token）

## 参考
- OpenPose 关键点格式: https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/doc/02_output.md
- ControlNet OpenPose: Replicate 上搜 "controlnet openpose"
- IP-Adapter: https://replicate.com/zsxkib/ip-adapter-sdxl
