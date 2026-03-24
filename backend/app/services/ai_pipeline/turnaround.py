"""
Turnaround Service — Generate front/side/back views from a single character image.

Supports two modes:
  - "replicate": calls Zero123++ via Replicate API
  - "mock": generates color-overlay placeholders (no API key needed)

Caching: uses image content hash to avoid regenerating views for the same image.
"""
import asyncio
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Optional

from .providers.mock_provider import MockProvider
from .providers.replicate_provider import ReplicateProvider

logger = logging.getLogger(__name__)

TURNAROUND_DIR = Path("static/turnarounds")


def _compute_image_hash(image_path: str) -> str:
    """Compute SHA-256 hash of image file contents."""
    h = hashlib.sha256()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]  # 16-char prefix is enough


class TurnaroundService:
    def __init__(self, api_token: Optional[str] = None, provider: str = "auto"):
        if provider == "auto":
            provider = "replicate" if api_token else "mock"

        if provider == "replicate":
            if not api_token:
                raise ValueError("Replicate API token required for replicate provider")
            self._provider = ReplicateProvider(api_token)
        else:
            self._provider = MockProvider()

        self._provider_name = provider
        TURNAROUND_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def provider_name(self) -> str:
        return self._provider_name

    async def generate_views(self, image_path: str) -> dict:
        """
        Generate (or return cached) three views from a single image.

        Returns:
            {
                "turnaround_id": "<hash>",
                "provider": "mock" | "replicate",
                "cached": bool,
                "views": {
                    "front": "/static/turnarounds/<hash>/front.png",
                    "side":  "/static/turnarounds/<hash>/side.png",
                    "back":  "/static/turnarounds/<hash>/back.png",
                }
            }
        """
        image_hash = await asyncio.to_thread(_compute_image_hash, image_path)
        output_dir = TURNAROUND_DIR / image_hash

        # Check cache
        cached_views = self._check_cache(output_dir)
        if cached_views:
            logger.info(f"Turnaround cache hit: {image_hash}")
            return {
                "turnaround_id": image_hash,
                "provider": self._provider_name,
                "cached": True,
                "views": cached_views,
            }

        # Generate
        output_dir.mkdir(parents=True, exist_ok=True)
        view_paths = await self._provider.generate(image_path, str(output_dir))

        views = {}
        for view_name, local_path in view_paths.items():
            rel = Path(local_path).relative_to(Path.cwd())
            views[view_name] = f"/{rel}"

        logger.info(f"Turnaround generated: {image_hash} ({self._provider_name})")
        return {
            "turnaround_id": image_hash,
            "provider": self._provider_name,
            "cached": False,
            "views": views,
        }

    def _check_cache(self, output_dir: Path) -> Optional[dict]:
        """Return cached view paths if all 3 views exist, else None."""
        if not output_dir.exists():
            return None

        views = {}
        for view_name in ("front", "side", "back"):
            path = output_dir / f"{view_name}.png"
            if not path.exists():
                return None
            rel = path.relative_to(Path.cwd())
            views[view_name] = f"/{rel}"
        return views
