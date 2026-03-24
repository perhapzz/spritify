# Sprint 2 — Pose-Conditioned Frame Generation

**Status:** ✅ COMPLETED  
**Date:** 2026-03-24

---

## Task 1: OpenPose Pose Library ✅

### Pose data created
```
backend/pose_data/
├── walk/   (8 frames)
├── run/    (8 frames)
├── idle/   (4 frames)
└── jump/   (8 frames)
```
Each frame is standard OpenPose 18-keypoint JSON (normalized 0-1 coords).

### PoseLibrary service
- `get_pose_sequence(motion_id, frame_count)` — loads + resamples frames
- `list_motions()` — returns available motions with metadata
- Generator script: `backend/generate_poses.py`

---

## Task 2: PoseFrameService ✅

`backend/app/services/ai_pipeline/pose_frames.py`:
- Takes turnaround views + motion_id → generates per-frame images
- Selects reference view (front/side/back) based on frame position
- Renders OpenPose skeleton → passes to provider
- Mock: blends reference + pose overlay
- Replicate: ControlNet + IP-Adapter (ready, awaiting token)

---

## Task 3: Generate Endpoint — Full AI Flow ✅

`POST /api/v1/generate` (mode=ai) now does:
1. **10%** Upload saved
2. **30%** Turnaround views generated (TurnaroundService)
3. **50%** Pose frames generating (PoseFrameService)
4. **80%** Frames done, composing sprite sheet
5. **100%** Sprite sheet ready → `result_url`

`GET /api/v1/motions?mode=ai` returns pose library motions.

---

## Task 4: Pose Renderer ✅

`backend/app/services/ai_pipeline/pose_renderer.py`:
- Renders 18-keypoint skeleton as colored lines on black background
- Standard OpenPose color scheme per limb
- Output used as ControlNet conditioning input

---

## Files Created/Modified
- `backend/pose_data/` — 28 JSON files (walk×8, run×8, idle×4, jump×8)
- `backend/generate_poses.py` — pose sequence generator script
- `backend/app/services/pose_library.py` (new)
- `backend/app/services/ai_pipeline/pose_frames.py` (implemented)
- `backend/app/services/ai_pipeline/pose_renderer.py` (new)
- `backend/app/services/ai_pipeline/providers/mock_provider.py` (added generate_pose_frame)
- `backend/app/services/ai_pipeline/providers/replicate_provider.py` (added generate_pose_frame)
- `backend/app/services/ai_pipeline/__init__.py` (exports PoseFrameService)
- `backend/app/api/generation.py` (full AI pipeline flow)
- `backend/app/main.py` (static/frames dir)
