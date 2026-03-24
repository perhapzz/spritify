"""
Turnaround API — generate front/side/back views from a single character image.
"""
import os
import uuid
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image as PILImage

from app.config import settings
from app.services.ai_pipeline import TurnaroundService

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSION = 4096


@router.post("/turnaround")
async def generate_turnaround(
    image: UploadFile = File(...),
):
    """
    Upload a character image and generate three views (front, side, back).
    Uses Replicate API if token is configured, otherwise mock mode.
    """
    # Validate content type
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Read and validate size
    content = await image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10MB")

    # Save upload
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(image.filename or "image.png")[1]
    input_path = os.path.join(upload_dir, f"{file_id}{ext}")

    with open(input_path, "wb") as f:
        f.write(content)

    # Validate image
    try:
        with PILImage.open(input_path) as img:
            w, h = img.size
            if w > MAX_DIMENSION or h > MAX_DIMENSION:
                os.remove(input_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Image dimensions {w}x{h} exceed max {MAX_DIMENSION}x{MAX_DIMENSION}",
                )
    except HTTPException:
        raise
    except Exception:
        os.remove(input_path)
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Generate views
    try:
        service = TurnaroundService(
            api_token=settings.replicate_api_token,
            provider=settings.ai_provider,
        )
        result = await service.generate_views(input_path)
        return result
    except Exception as e:
        logger.error(f"Turnaround generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")
