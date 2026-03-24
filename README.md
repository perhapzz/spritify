# Spritify - AI Sprite Sheet Generator

将静态的动物/玩偶图片转换为游戏可用的 Sprite Sheet（精灵表）动画。

## 项目概述

用户上传一张静态角色图片，系统自动生成该角色的多个动作帧，输出标准的 sprite sheet 格式，可直接用于游戏开发。

## 技术栈

### 后端
- **Python 3.11+**
- **FastAPI** - Web API 框架
- **AnimatedDrawings** - Meta 开源的动画生成引擎
- **Pillow** - 图像处理
- **Celery + Redis** (可选) - 异步任务队列

### 前端
- **React 18** + **TypeScript**
- **Vite** - 构建工具
- **TailwindCSS** - 样式
- **React Query** - 数据获取

### AI 引擎
- **AnimatedDrawings** - 骨骼检测 + 动作重定向
- **BVH 动作库** (Mixamo) - 预置动作数据

## 功能规划

### MVP (Phase 1)
- [ ] 用户上传图片
- [ ] 选择预置动作 (walk, run, idle, jump)
- [ ] 生成 sprite sheet
- [ ] 下载 PNG 格式

### Phase 2
- [ ] 自定义帧数/尺寸
- [ ] 预览动画效果
- [ ] 支持更多动作
- [ ] 用户账户系统

### Phase 3
- [ ] 批量生成
- [ ] API 接口供外部调用
- [ ] 自定义动作上传 (BVH)

## 项目结构

```
spritify/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI 入口
│   │   ├── api/
│   │   │   └── generation.py # 生成接口
│   │   ├── services/
│   │   │   ├── animator.py   # AnimatedDrawings 集成
│   │   │   └── sprite_sheet.py # Sprite 拼接
│   │   └── utils/
│   ├── static/
│   │   ├── uploads/          # 用户上传
│   │   └── outputs/          # 生成结果
│   ├── motion_data/          # BVH 动作文件
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── api/
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml
└── README.md
```

## API 设计

### 获取可用动作
```
GET /api/v1/motions
Response: { motions: [{ id, name, description }] }
```

### 生成 Sprite Sheet
```
POST /api/v1/generate
Body: FormData { image, motion_id, frame_count?, frame_size? }
Response: { task_id, status }
```

### 查询生成状态
```
GET /api/v1/status/{task_id}
Response: { task_id, status, progress, result_url? }
```

### 下载结果
```
GET /api/v1/download/{task_id}
Response: PNG file
```

## 开发计划

### Week 1: 基础框架
- [x] 项目结构搭建
- [ ] 后端 API 框架
- [ ] 前端界面框架
- [ ] AnimatedDrawings 集成测试

### Week 2: 核心功能
- [ ] 图片上传处理
- [ ] AnimatedDrawings 完整集成
- [ ] Sprite sheet 生成
- [ ] 基础前端 UI

### Week 3: 完善体验
- [ ] 动画预览
- [ ] 错误处理
- [ ] 加载状态
- [ ] Docker 部署


## Azure 部署架构

```
                    ┌─────────────────────────────────────────┐
                    │           Azure Front Door              │
                    │         (CDN + WAF + SSL)               │
                    └──────────────┬──────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Static Web App  │    │ Container App    │    │  Blob Storage    │
│    (Frontend)    │    │   (Backend)      │    │ (uploads/outputs)│
│    React SPA     │    │   FastAPI        │    │                  │
└──────────────────┘    └────────┬─────────┘    └──────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
           ┌─────────────┐ ┌──────────┐ ┌──────────────┐
           │ Redis Cache │ │ Queue    │ │ Container    │
           │ (sessions)  │ │ Storage  │ │ Registry     │
           └─────────────┘ └──────────┘ └──────────────┘
```

### Azure 服务选型

| 组件 | Azure 服务 | 预估月成本 |
|------|-----------|-----------|
| 前端托管 | Static Web Apps (Free tier) | $0 |
| 后端 API | Container Apps | ~$20-50 |
| 文件存储 | Blob Storage | ~$5 |
| 缓存 | Redis Cache (Basic) | ~$15 |
| 任务队列 | Queue Storage | ~$1 |
| 域名/SSL | Front Door | ~$35 |
| **合计** | | **~$76-106/月** |

### 简化方案（MVP）

| 组件 | Azure 服务 | 预估月成本 |
|------|-----------|-----------|
| 前端 | Static Web Apps | $0 |
| 后端 | Container Apps (单实例) | ~$20 |
| 存储 | Blob Storage | ~$5 |
| **合计** | | **~$25/月** |

## 环境配置

### 环境变量
```bash
# Azure
AZURE_STORAGE_CONNECTION_STRING=
AZURE_STORAGE_CONTAINER_UPLOADS=uploads
AZURE_STORAGE_CONTAINER_OUTPUTS=outputs

# App
API_URL=https://api.spritify.com
ALLOWED_ORIGINS=https://spritify.com

# Redis (可选)
REDIS_URL=
```

### 本地开发
```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### Docker 构建
```bash
# 构建后端
docker build -t spritify-backend ./backend

# 本地测试
docker-compose up
```

### Azure 部署
```bash
# 登录 Azure
az login

# 创建资源组
az group create --name spritify-rg --location eastasia

# 部署 (使用 Bicep/ARM 模板)
az deployment group create \
  --resource-group spritify-rg \
  --template-file infra/main.bicep
```
