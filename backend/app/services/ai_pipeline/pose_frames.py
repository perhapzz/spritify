"""
PoseFrameService — generates animation frames from turnaround views + OpenPose sequences.
"""
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Optional

from PIL import Image

from app.services.pose_library import PoseLibrary
from .pose_renderer import render_pose_image

logger = logging.getLogger(__name__)

FRAMES_DIR = Path("static/frames")


class PoseFrameService:
    def __init__(self, provider):
        """
        Args:
            provider: a MockProvider or ReplicateProvider instance
        """
        self._provider = provider
        self._pose_lib = PoseLibrary()
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_frames(
        self,
        turnaround_views: dict,  # {"front": path, "side": path, "back": path}
        motion_id: str,
        frame_count: int = 8,
        frame_size: int = 128,
    ) -> list[str]:
        """
        Generate animation frames using turnaround views + pose sequence.

        Returns: list of file paths for each frame image.
        """
        # 1. Get pose sequence
        pose_sequence = self._pose_lib.get_pose_sequence(motion_id, frame_count)
        logger.info(f"Loaded {len(pose_sequence)} pose frames for '{motion_id}'")

        # 2. Generate output dir
        batch_id = str(uuid.uuid4())
        output_dir = FRAMES_DIR / batch_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # 3. Generate each frame
        frame_paths = []
        for i, pose_data in enumerate(pose_sequence):
            keypoints = pose_data["people"][0]["pose_keypoints_2d"]

            # Choose reference view based on frame index
            # Simple heuristic: mostly front, some side frames
            ref_view = self._select_reference_view(i, len(pose_sequence))
            ref_path = turnaround_views.get(ref_view, turnaround_views["front"])

            # Render pose skeleton image
            pose_img = await asyncio.to_thread(
                render_pose_image, keypoints, frame_size, frame_size
            )
            pose_img_path = str(output_dir / f"pose_{i}.png")
            pose_img.save(pose_img_path)

            # Generate frame via provider
            frame_path = str(output_dir / f"frame_{i}.png")
            await self._provider.generate_pose_frame(
                reference_image=ref_path,
                pose_image=pose_img_path,
                output_path=frame_path,
                frame_size=frame_size,
            )
            frame_paths.append(frame_path)
            logger.info(f"Frame {i}/{len(pose_sequence)} generated (ref={ref_view})")

        return frame_paths

    def _select_reference_view(self, frame_idx: int, total_frames: int) -> str:
        """
        Select which turnaround view to use as reference for a given frame.
        For side-scrolling sprites, most frames use 'side' view.
        """
        # Default: use side view for movement, front for idle-like frames
        # This is a simple heuristic; can be made motion-aware later
        ratio = frame_idx / max(total_frames - 1, 1)
        if ratio < 0.15 or ratio > 0.85:
            return "front"
        elif 0.4 < ratio < 0.6:
            return "back"
        else:
            return "side"
