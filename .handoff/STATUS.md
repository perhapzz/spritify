# Sprint 1 — Status

**Status:** ✅ COMPLETED  
**Date:** 2026-03-24

---

## Task 1: AI Pipeline Core ✅

### 1.1 Directory structure created
```
backend/app/services/ai_pipeline/
├── __init__.py
├── turnaround.py              # TurnaroundService
├── pose_frames.py             # Placeholder for Sprint 2
└── providers/
    ├── __init__.py
    ├── mock_provider.py       # Color-overlay mock (no API key)
    └── replicate_provider.py  # Zero123++ via Replicate
```

### 1.2 TurnaroundService
- Auto-detects provider: Replicate if `REPLICATE_API_TOKEN` set, mock otherwise
- Returns `turnaround_id` + view URLs (front/side/back)
- Mock mode: tinted copies with FRONT/SIDE/BACK labels

### 1.3 ReplicateProvider
- Calls `stability-ai/zero123plus` model
- Downloads 3×2 grid output, crops front/side/back cells
- All blocking calls wrapped in `asyncio.to_thread()`

### 1.4 `POST /api/v1/turnaround` endpoint
- Input validation (size ≤10MB, dimensions ≤4096²)
- Returns view paths

### 1.5 Config updated
- `replicate_api_token` (env: `REPLICATE_API_TOKEN`)
- `ai_provider` ("replicate" | "mock" | "auto")

---

## Task 2: Generate endpoint refactored ✅
- `POST /api/v1/generate` now accepts `mode` param: `"ai"` (default) or `"classic"`
- `mode=ai`: runs TurnaroundService, returns view URLs
- `mode=classic`: runs AnimatedDrawings pipeline (existing behavior)
- `GenerationStatus` model has new `turnaround` field for AI mode

---

## Task 3: AD bug fixes ✅ (done in previous commit)
- `jumping_jacks` retarget: `cmu1_bvh.yaml` → `cmu1_pfp.yaml`
- Blocking calls wrapped with `asyncio.to_thread()`
- Input validation added
- Silent fallback removed
- Mesa headless configured in Dockerfile

---

## Files Modified/Created
- `backend/app/services/ai_pipeline/` (new directory, 6 files)
- `backend/app/api/turnaround.py` (new)
- `backend/app/api/generation.py` (refactored)
- `backend/app/config.py` (AI settings added)
- `backend/app/main.py` (turnaround router registered)
- `backend/requirements.txt` (replicate added)
