from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import logging
import traceback
from PIL import Image as PILImage

from app.services.animator import AnimatorService
from app.services.sprite_sheet import SpriteSheetService
from app.services.ai_pipeline import TurnaroundService, PoseFrameService
from app.services.ai_pipeline.providers.mock_provider import MockProvider
from app.services.ai_pipeline.providers.replicate_provider import ReplicateProvider
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSION = 4096


@router.get("/motions")
async def list_motions(mode: str = "ai"):
    """List all available motion presets"""
    if mode == "classic":
        animator = AnimatorService()
        return {"motions": animator.get_available_motions(), "mode": "classic"}
    else:
        from app.services.pose_library import PoseLibrary
        lib = PoseLibrary()
        return {"motions": lib.list_motions(), "mode": "ai"}


class GenerationRequest(BaseModel):
    motion_id: str
    frame_count: Optional[int] = 8
    frame_size: Optional[int] = 128


class GenerationStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None
    result_url: Optional[str] = None
    turnaround: Optional[dict] = None  # AI mode: view URLs
    error: Optional[str] = None


# In-memory task storage (use Redis in production)
tasks: dict[str, GenerationStatus] = {}


@router.post("/generate")
async def generate_sprite(
    image: UploadFile = File(...),
    motion_id: str = "dab",
    frame_count: int = 8,
    frame_size: int = 128,
    mode: str = "ai",  # "ai" (new pipeline) | "classic" (AnimatedDrawings)
    turnaround_id: Optional[str] = None,  # reuse cached turnaround
):
    """
    Upload an image and generate a sprite sheet with the specified motion.
    This runs synchronously for simplicity.
    """
    # Validate file type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read content and validate file size
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Save uploaded file
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(image.filename or "image.png")[1]
    input_path = os.path.join(upload_dir, f"{task_id}{file_ext}")

    with open(input_path, "wb") as f:
        f.write(content)

    # Validate image can be opened and check dimensions
    try:
        with PILImage.open(input_path) as img:
            w, h = img.size
            if w > MAX_DIMENSION or h > MAX_DIMENSION:
                os.remove(input_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Image dimensions {w}x{h} exceed maximum {MAX_DIMENSION}x{MAX_DIMENSION}"
                )
    except HTTPException:
        raise
    except Exception:
        os.remove(input_path)
        raise HTTPException(status_code=400, detail="Invalid image file — could not be opened")

    # Initialize task
    tasks[task_id] = GenerationStatus(
        task_id=task_id,
        status="processing",
        progress=10
    )

    try:
        if mode == "ai":
            # --- AI Pipeline: turnaround → pose frames → sprite sheet ---

            # Resolve provider
            provider_name = settings.ai_provider
            if provider_name == "auto":
                provider_name = "replicate" if settings.replicate_api_token else "mock"

            if provider_name == "replicate":
                provider = ReplicateProvider(settings.replicate_api_token)
            else:
                provider = MockProvider()

            # Step 1: Generate turnaround views (30%) — or reuse cached
            turnaround_svc = TurnaroundService(
                api_token=settings.replicate_api_token,
                provider=settings.ai_provider,
            )
            tasks[task_id].progress = 30

            if turnaround_id:
                # Try to reuse cached turnaround
                from pathlib import Path as _P
                cache_dir = _P("static/turnarounds") / turnaround_id
                cached = turnaround_svc._check_cache(cache_dir)
                if cached:
                    turnaround_views = cached
                    logger.info(f"[AI] Reusing cached turnaround: {turnaround_id}")
                else:
                    logger.info(f"[AI] Cache miss for {turnaround_id}, regenerating")
                    turnaround = await turnaround_svc.generate_views(input_path)
                    turnaround_views = turnaround["views"]
            else:
                logger.info(f"[AI] Step 1/3: Generating turnaround views")
                turnaround = await turnaround_svc.generate_views(input_path)
                turnaround_views = turnaround["views"]

            tasks[task_id].turnaround = turnaround_views
            logger.info(f"[AI] Turnaround ready")

            # Step 2: Generate pose-conditioned frames (50% → 80%)
            tasks[task_id].progress = 50
            logger.info(f"[AI] Step 2/3: Generating {frame_count} pose frames for '{motion_id}'")

            # Resolve view paths to absolute
            from pathlib import Path as _Path
            abs_views = {}
            for k, v in turnaround_views.items():
                p = v.lstrip("/")
                abs_views[k] = str(_Path(p).resolve()) if _Path(p).exists() else p

            pose_svc = PoseFrameService(provider=provider)
            frame_paths = await pose_svc.generate_frames(
                turnaround_views=abs_views,
                motion_id=motion_id,
                frame_count=frame_count,
                frame_size=frame_size,
            )
            tasks[task_id].progress = 80
            logger.info(f"[AI] Generated {len(frame_paths)} frames")

            # Step 3: Compose sprite sheet (80% → 100%)
            from PIL import Image as _PILImg
            frames = [_PILImg.open(p).convert("RGBA") for p in frame_paths]

            sprite_service = SpriteSheetService()
            output_dir = "static/outputs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/{task_id}_sprite.png"

            await sprite_service.create_sprite_sheet(
                frames=frames,
                output_path=output_path,
                frame_size=frame_size,
            )

            tasks[task_id].progress = 100
            tasks[task_id].status = "completed"
            tasks[task_id].result_url = f"/static/outputs/{task_id}_sprite.png"
            logger.info(f"[AI] Sprite sheet saved: {output_path}")

        else:
            # --- Classic mode: AnimatedDrawings ---
            animator = AnimatorService()
            sprite_service = SpriteSheetService()

            tasks[task_id].progress = 30
            logger.info(f"[Classic mode] Generating frames for task {task_id}")

            frames = await animator.generate_frames(
                input_path=input_path,
                motion_id=motion_id,
                frame_count=frame_count,
            )

            logger.info(f"Generated {len(frames)} frames")
            tasks[task_id].progress = 70

            output_dir = "static/outputs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/{task_id}_sprite.png"

            await sprite_service.create_sprite_sheet(
                frames=frames,
                output_path=output_path,
                frame_size=frame_size,
            )

            logger.info(f"Sprite sheet saved to {output_path}")
            tasks[task_id].progress = 100
            tasks[task_id].status = "completed"
            tasks[task_id].result_url = f"/static/outputs/{task_id}_sprite.png"

            animator.cleanup()

    except Exception as e:
        logger.error(f"Error generating sprite: {e}")
        logger.error(traceback.format_exc())
        tasks[task_id].status = "failed"
        tasks[task_id].error = str(e)

    return tasks[task_id]


@router.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get the status of a generation task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]


@router.get("/download/{task_id}")
async def download_result(task_id: str):
    """Download the generated sprite sheet"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed")

    output_path = f"static/outputs/{task_id}_sprite.png"
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        output_path,
        media_type="image/png",
        filename=f"sprite_{task_id}.png"
    )
