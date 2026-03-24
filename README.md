# 🎮 Spritify

Transform static character images into animated sprite sheets using AI.

## How It Works

```
Upload Image → AI generates 3 views (front/side/back)
                    ↓
            Select animation (walk/run/idle/jump)
                    ↓
            Pose-conditioned frame generation
                    ↓
            Sprite sheet + GIF download
```

## Two Modes

| Mode | How | Best For |
|------|-----|----------|
| **⚡ AI HD** | Multi-view generation → pose-conditioned frames | High-quality, consistent characters |
| **🚀 Classic** | AnimatedDrawings bone deformation | Quick results, simple animations |

## Quick Start

### Docker (recommended)

```bash
docker-compose up
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Enable AI Mode

Set your Replicate API token to use real AI generation:

```bash
export REPLICATE_API_TOKEN=r8_your_token_here
```

Without a token, Spritify runs in **mock mode** — the full pipeline works with placeholder outputs.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/turnaround` | POST | Generate front/side/back views from image |
| `/api/v1/generate` | POST | Full pipeline: image → sprite sheet |
| `/api/v1/motions` | GET | List available animations |
| `/api/v1/status/{id}` | GET | Check generation status |
| `/api/v1/download/{id}` | GET | Download sprite sheet PNG |

### Generate Parameters

```
image: File (required)
motion_id: walk | run | idle | jump (AI) or dab | jumping | wave_hello | zombie | jumping_jacks | jesse_dance (Classic)
frame_count: 4-16 (default: 8)
frame_size: 64-512 (default: 128)
mode: ai | classic (default: ai)
turnaround_id: string (optional, reuse cached turnaround)
```

## Architecture

```
frontend/          React 19 + TypeScript + TailwindCSS v4
backend/
  app/
    api/           FastAPI endpoints
    services/
      ai_pipeline/ AI generation (turnaround + pose frames)
        providers/   Replicate API + Mock fallback
      animator.py  Classic mode (AnimatedDrawings)
      pose_library.py  OpenPose keypoint sequences
      sprite_sheet.py  Frame → sprite sheet composition
  pose_data/       Pre-defined walk/run/idle/jump sequences
```

## Tech Stack

- **Frontend:** React 19, TypeScript, TailwindCSS v4, Vite
- **Backend:** FastAPI, Python 3.11, Pillow
- **AI:** Replicate API (Zero123++, ControlNet + IP-Adapter)
- **Classic:** AnimatedDrawings (Meta Research)
- **Deploy:** Docker Compose, Nginx

## License

MIT
