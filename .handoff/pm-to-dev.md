# Task: Sprint 5 — Deploy to perhapzz-services VM

Priority: P0 | Status: PENDING

## Target
- **VM:** perhapzz-services (20.205.124.180)
- **SSH:** `ssh azureuser@20.205.124.180`
- **Docker:** 29.3.0 + Compose v5.1.1 已安装
- **资源:** 4GB RAM, ~9GB 磁盘可用

## 部署方案
Docker Compose 部署，Nginx 反代。

## Step 1: 推送代码到 VM

在部署 VM 上 clone 项目：
```bash
ssh azureuser@20.205.124.180
cd ~
git clone https://perhapzz@github.com/perhapzz/spritify.git
cd spritify
```

## Step 2: 确保 Docker 配置正确

检查 `docker-compose.yml`，确保：
- backend 端口 8000
- frontend 端口 3000（或直接 80）
- 环境变量 `AI_PROVIDER=mock`
- volume 映射正确

如果需要 Nginx 反代（推荐），创建 `nginx.conf`：
```
前端: http://20.205.124.180/ → frontend:3000
后端 API: http://20.205.124.180/api/ → backend:8000/api/
静态文件: http://20.205.124.180/static/ → backend:8000/static/
```

或者简化方案：直接在 docker-compose 里加 nginx 服务。

## Step 3: Build & Run

```bash
ssh azureuser@20.205.124.180
cd ~/spritify
docker compose up -d --build
```

验证：
- `curl http://localhost:8000/health` → `{"status": "healthy"}`
- `curl http://localhost:3000` → 前端 HTML
- 浏览器访问 `http://20.205.124.180` → Spritify 页面

## Step 4: 防火墙/端口

确保 VM 的 NSG（网络安全组）开放了 80 端口（或 3000+8000）。
可以用 `az` 或者提示用户去 Azure Portal 手动开。

如果无法操作 NSG，至少确保 Docker 启动成功，端口在 VM 本地可访问。

## ⚠️ 注意
- **所有部署操作在 20.205.124.180 上执行**，不要在本机（OpenClaw VM）部署
- 用 `ssh azureuser@20.205.124.180` 远程操作
- git 操作用 perhapzz 账号
- 磁盘空间有限（~9GB），注意 Docker image 大小

## Acceptance Criteria
- [ ] 代码 clone 到 perhapzz-services VM
- [ ] `docker compose up -d` 成功启动
- [ ] 后端 health check 通过
- [ ] 前端页面可访问
- [ ] 完整流程可跑通（Mock 模式）
