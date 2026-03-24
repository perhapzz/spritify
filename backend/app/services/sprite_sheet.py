"""
Sprite Sheet Service - Combines frames into a sprite sheet
"""
from typing import List
from PIL import Image
import math


class SpriteSheetService:
    async def create_sprite_sheet(
        self,
        frames: List[Image.Image],
        output_path: str,
        frame_size: int = 128,
        columns: int = None,
    ) -> str:
        """
        Combine multiple frames into a single sprite sheet image.

        Args:
            frames: List of PIL Image frames
            output_path: Where to save the sprite sheet
            frame_size: Size of each frame (will be resized)
            columns: Number of columns (auto-calculated if None)

        Returns:
            Path to the created sprite sheet
        """
        if not frames:
            raise ValueError("No frames provided")

        frame_count = len(frames)

        # Calculate grid dimensions
        if columns is None:
            columns = min(frame_count, 8)
        rows = math.ceil(frame_count / columns)

        # Create sprite sheet canvas
        sheet_width = columns * frame_size
        sheet_height = rows * frame_size
        sprite_sheet = Image.new("RGBA", (sheet_width, sheet_height), (0, 0, 0, 0))

        # Place each frame
        for i, frame in enumerate(frames):
            # Resize frame to target size
            resized = self._resize_frame(frame, frame_size)

            # Calculate position
            col = i % columns
            row = i // columns
            x = col * frame_size
            y = row * frame_size

            # Paste frame onto sheet
            sprite_sheet.paste(resized, (x, y))

        # Save sprite sheet
        sprite_sheet.save(output_path, "PNG")
        return output_path

    def _resize_frame(self, frame: Image.Image, target_size: int) -> Image.Image:
        """
        Resize a frame to fit within target_size while maintaining aspect ratio,
        then center it on a transparent canvas.
        """
        # Calculate new size maintaining aspect ratio
        width, height = frame.size
        ratio = min(target_size / width, target_size / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)

        # Resize
        resized = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Center on canvas
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        x = (target_size - new_width) // 2
        y = (target_size - new_height) // 2
        canvas.paste(resized, (x, y))

        return canvas

    async def extract_frames_from_gif(
        self,
        gif_path: str,
        max_frames: int = None,
    ) -> List[Image.Image]:
        """
        Extract frames from an animated GIF.
        Useful for processing AnimatedDrawings output.
        """
        frames = []
        with Image.open(gif_path) as gif:
            for i in range(gif.n_frames):
                if max_frames and i >= max_frames:
                    break
                gif.seek(i)
                frames.append(gif.copy().convert("RGBA"))
        return frames
