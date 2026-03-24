"""
Turnaround Service — Generate front/side/back views from a single character image.

Supports two modes:
  - "replicate": calls Zero123++ via Replicate API
  - "mock": generates color-overlay placeholders (no API key needed)
"""
import asyncio
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from .providers.mock_provider import MockProvider
from .providers.replicate_provider import ReplicateProvider

logger = logging.getLogger(__name__)

TURNAROUND_DIR = Path("static/turnarounds")


class TurnaroundService:
    def __init__(self, api_token: Optional[str] = None, provider: str = "auto"):
        """
        Args:
            api_token: Replicate API token. If None, falls back to mock.
            provider: "replicate" | "mock" | "auto" (auto = replicate if token else mock)
        """
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
        Generate three views (front, side, back) from a single image.

        Returns:
            {
                "turnaround_id": "...",
                "provider": "mock" | "replicate",
                "views": {
                    "front": "/static/turnarounds/<id>_front.png",
                    "side":  "/static/turnarounds/<id>_side.png",
                    "back":  "/static/turnarounds/<id>_back.png",
                }
            }
        """
        turnaround_id = str(uuid.uuid4())
        output_dir = TURNAROUND_DIR / turnaround_id
        output_dir.mkdir(parents=True, exist_ok=True)

        view_paths = await self._provider.generate(image_path, str(output_dir))

        # Build URL-safe paths
        views = {}
        for view_name, local_path in view_paths.items():
            rel = Path(local_path).relative_to(Path.cwd())
            views[view_name] = f"/{rel}"

        return {
            "turnaround_id": turnaround_id,
            "provider": self._provider_name,
            "views": views,
        }
