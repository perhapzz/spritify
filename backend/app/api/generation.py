from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import asyncio
import logging
import traceback
from PIL import Image as PILImage

from app.services.animator import AnimatorService
from app.services.sprite_sheet import SpriteSheetService

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSION = 4096


@router.get("/motions")
async def list_motions():
    """List all available motion presets"""
    animator = AnimatorService()
    return {"motions": animator.get_available_motions()}


class GenerationRequest(BaseModel):
    motion_id: str
    frame_count: Optional[int] = 8
    frame_size: Optional[int] = 128


class GenerationStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[int] = None
    result_url: Optional[str] = None
    error: Optional[str] = None


# In-memory task storage (use Redis in production)
tasks: dict[str, GenerationStatus] = {}


@router.post("/generate")
async def generate_sprite(
    image: UploadFile = File(...),
    motion_id: str = "dab",
    frame_count: int = 8,
    frame_size: int = 128,
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
        # Initialize services
        animator = AnimatorService()
        sprite_service = SpriteSheetService()

        # Generate animation frames
        tasks[task_id].progress = 30
        logger.info(f"Generating frames for task {task_id}")

        frames = await animator.generate_frames(
            input_path=input_path,
            motion_id=motion_id,
            frame_count=frame_count,
        )

        logger.info(f"Generated {len(frames)} frames")
        tasks[task_id].progress = 70

        # Create sprite sheet
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

        # Clean up temp files
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
