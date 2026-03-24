# Task: Fix Backend Critical Issues — Sprint 1, Task 1

Priority: P0 | Status: PENDING

## Context
I've reviewed the full Spritify codebase. The architecture is solid — FastAPI + AnimatedDrawings + React frontend. But there are several critical issues preventing the pipeline from working end-to-end. Let's fix them.

## What to Do

### 1. Fix `jumping_jacks` retarget config
**File:** `backend/app/services/animator.py`

The `MOTION_CONFIGS["jumping_jacks"]` references `"examples/config/retarget/cmu1_bvh.yaml"` which doesn't exist. Check what retarget configs actually exist in `animated_drawings_lib/examples/config/retarget/` and use the correct one (likely `cmu1_pfp.yaml`).

### 2. Wrap blocking calls with `asyncio.to_thread()`
**File:** `backend/app/services/animator.py`

`animated_drawings.render.start()` is CPU-bound and blocks the FastAPI event loop. Wrap it:
```python
await asyncio.to_thread(animated_drawings.render.start, str(mvc_cfg_path))
```

Same for `create_character_annotations()` — it does OpenCV/MediaPipe work.

### 3. Add input validation
**File:** `backend/app/api/generation.py`

Add these checks at the start of `generate_sprite()`:
- File size ≤ 10MB
- Image is valid (can be opened by Pillow)
- Dimensions ≤ 4096×4096
- Return clear 400 errors with descriptive messages

### 4. Configure headless rendering (Mesa)
**File:** `backend/app/services/animator.py`

Add to the MVC config dict in `_generate_with_animated_drawings`:
```python
mvc_cfg["view"] = {"USE_MESA": True}
```

**File:** `backend/Dockerfile` — add Mesa deps:
```dockerfile
RUN apt-get update && apt-get install -y libosmesa6-dev libgl1-mesa-dev
ENV PYOPENGL_PLATFORM=osmesa
```

### 5. Improve error handling — stop silent fallback
**File:** `backend/app/services/animator.py`

In `generate_frames()`, the current code catches all exceptions and falls back to a placeholder bounce animation. This is confusing for users. Change it to:
- Try AnimatedDrawings pipeline
- If it fails, return a proper error (don't fall back silently)
- Keep the placeholder method but only use it if explicitly requested (e.g., `motion_id="demo"`)

**File:** `backend/app/api/generation.py`
- Catch the animator exception and return a meaningful error in the task status

### 6. Verify BVH files exist
Quick sanity check — make sure all BVH files referenced in `MOTION_CONFIGS` actually exist at their paths under `animated_drawings_lib/`.

## Acceptance Criteria
- [ ] All 6 motions reference valid config files
- [ ] Generation doesn't block the event loop
- [ ] Invalid images return clear 400 errors
- [ ] Mesa headless rendering is configured
- [ ] No silent fallback to placeholder — errors are surfaced
- [ ] Backend starts without errors: `cd backend && uvicorn app.main:app`

## Notes
- The animated_drawings_lib is at `spritify/animated_drawings_lib/` (sibling to `backend/`)
- Don't restructure the project — just fix these issues in-place
- Commit when done and update `.handoff/STATUS.md`
