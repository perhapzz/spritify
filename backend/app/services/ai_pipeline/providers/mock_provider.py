"""
Mock Provider — generates color-overlay placeholders so the full pipeline
can be tested end-to-end without any API key.
"""
import asyncio
import math
from pathlib import Path
from PIL import Image, ImageDraw
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
            bbox = draw.textbbox((0, 0), label)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (img.width - tw) // 2
            draw.text((x, 10), label, fill=(255, 255, 255, 200))

            path = out / f"{view_name}.png"
            img.save(str(path))
            results[view_name] = str(path)
            logger.info(f"Mock view generated: {view_name} → {path}")

        return results

    async def generate_pose_frame(
        self,
        reference_image: str,
        pose_image: str,
        output_path: str,
        frame_size: int = 128,
    ) -> None:
        """
        Mock pose-conditioned frame generation.
        Takes reference image, applies a transform based on the pose skeleton overlay.
        """
        await asyncio.to_thread(
            self._generate_pose_frame_sync,
            reference_image, pose_image, output_path, frame_size,
        )

    def _generate_pose_frame_sync(
        self, reference_image: str, pose_image: str, output_path: str, frame_size: int
    ) -> None:
        # Load reference and pose
        ref = Image.open(reference_image).convert("RGBA")
        pose = Image.open(pose_image).convert("RGBA")

        # Resize reference to target
        ref = ref.resize((frame_size, frame_size), Image.Resampling.LANCZOS)
        pose = pose.resize((frame_size, frame_size), Image.Resampling.LANCZOS)

        # Blend: 85% reference + 15% pose overlay for visual feedback
        blended = Image.new("RGBA", (frame_size, frame_size), (0, 0, 0, 0))
        blended = Image.alpha_composite(blended, ref)

        # Make pose semi-transparent
        pose_overlay = pose.copy()
        alpha = pose_overlay.split()[3] if pose_overlay.mode == "RGBA" else None
        if alpha:
            import numpy as np
            arr = __import__('numpy').array(pose_overlay)
            arr[:, :, 3] = (arr[:, :, 3] * 0.3).astype('uint8')
            pose_overlay = Image.fromarray(arr)

        blended = Image.alpha_composite(blended, pose_overlay)
        blended.save(output_path)
        logger.info(f"Mock pose frame → {output_path}")
