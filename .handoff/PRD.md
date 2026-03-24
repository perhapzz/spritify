# Spritify - Product Requirements Document

## Vision
Upload a static character image → get an animated sprite sheet. Dead simple.

## MVP Scope (Phase 1)

### Must Have
1. **Upload image** — PNG/JPG/WebP, drag & drop or click
2. **Select motion** — 6 presets (dab, jump, wave, zombie, jumping jacks, dance)
3. **Configure** — frame count (4-16), frame size (64-512)
4. **Generate** — produce sprite sheet via AnimatedDrawings pipeline
5. **Preview** — animate the sprite sheet in-browser (canvas)
6. **Download** — PNG sprite sheet

### Should Have (MVP+)
- Background generation with real progress updates (not blocking the API)
- Error recovery — clear messages when pose detection fails
- GIF download option alongside PNG

### Out of Scope for MVP
- User accounts
- Batch generation
- Custom BVH upload
- Azure deployment (local-first)

## Architecture Decision
Keep current architecture — it's sound. Focus on making the pipeline reliable end-to-end.

## Key Issues Found in Code Review

### Critical
1. **`jumping_jacks` retarget config** references `cmu1_bvh.yaml` which doesn't exist — only `cmu1_pfp.yaml` exists
2. **Synchronous generation** blocks the FastAPI event loop — needs `asyncio.to_thread()` or background tasks
3. **AnimatedDrawings render** requires OpenGL context (Mesa/GLFW) — needs headless setup on server

### Important
4. **No input validation** on image dimensions/file size
5. **Placeholder fallback** silently returns bounce animation — user should know AD failed
6. **Frontend polling** is set up but API returns synchronously — mismatch
7. **No cleanup** of old uploads/outputs

### Nice to Have
8. Better motion previews (thumbnails/GIFs for each motion)
9. Speed indicator per motion
