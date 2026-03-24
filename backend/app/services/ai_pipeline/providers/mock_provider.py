"""
Mock Provider — generates color-overlay placeholders so the full pipeline
can be tested end-to-end without any API key.
"""
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# Color overlays per view (RGBA with low alpha for tint)
VIEW_COLORS = {
    "front": (0, 200, 0, 60),    # green tint
    "side":  (0, 100, 255, 60),   # blue tint
    "back":  (255, 60, 60, 60),   # red tint
}


class MockProvider:
    async def generate(self, image_path: str, output_dir: str) -> dict[str, str]:
        """
        Create 3 tinted copies of the input image as mock views.

        Returns: {"front": path, "side": path, "back": path}
        """
        return await asyncio.to_thread(self._generate_sync, image_path, output_dir)

    def _generate_sync(self, image_path: str, output_dir: str) -> dict[str, str]:
        original = Image.open(image_path).convert("RGBA")
        out = Path(output_dir)
        results = {}

        for view_name, color in VIEW_COLORS.items():
            img = original.copy()

            # Apply color overlay
            overlay = Image.new("RGBA", img.size, color)
            img = Image.alpha_composite(img, overlay)

            # Draw label
            draw = ImageDraw.Draw(img)
            label = view_name.upper()
            # Use default font, centered at top
            bbox = draw.textbbox((0, 0), label)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (img.width - tw) // 2
            draw.text((x, 10), label, fill=(255, 255, 255, 200))

            path = out / f"{view_name}.png"
            img.save(str(path))
            results[view_name] = str(path)
            logger.info(f"Mock view generated: {view_name} → {path}")

        return results
