"""
PoseLibrary — loads pre-defined OpenPose keypoint sequences from pose_data/.
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

POSE_DATA_DIR = Path(__file__).parent.parent.parent / "pose_data"

MOTION_META = {
    "walk": {"name": "Walk", "description": "Walking cycle", "default_frames": 8},
    "run":  {"name": "Run",  "description": "Running cycle", "default_frames": 8},
    "idle": {"name": "Idle", "description": "Idle breathing", "default_frames": 4},
    "jump": {"name": "Jump", "description": "Jump sequence",  "default_frames": 8},
}


class PoseLibrary:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or POSE_DATA_DIR

    def get_pose_sequence(self, motion_id: str, frame_count: Optional[int] = None) -> list[dict]:
        """
        Return OpenPose keypoint dicts for the given motion.
        If frame_count differs from stored frames, resample evenly.
        """
        motion_dir = self.data_dir / motion_id
        if not motion_dir.exists():
            raise ValueError(f"Unknown motion: {motion_id}. Available: {list(MOTION_META.keys())}")

        # Load all frames sorted
        files = sorted(motion_dir.glob("frame_*.json"), key=lambda f: int(f.stem.split("_")[1]))
        if not files:
            raise ValueError(f"No pose frames found in {motion_dir}")

        frames = []
        for f in files:
            with open(f) as fp:
                frames.append(json.load(fp))

        # Resample if needed
        if frame_count and frame_count != len(frames):
            step = len(frames) / frame_count
            frames = [frames[int(i * step) % len(frames)] for i in range(frame_count)]

        return frames

    def list_motions(self) -> list[dict]:
        """List available motions with metadata."""
        result = []
        for motion_id, meta in MOTION_META.items():
            motion_dir = self.data_dir / motion_id
            frame_files = list(motion_dir.glob("frame_*.json")) if motion_dir.exists() else []
            result.append({
                "id": motion_id,
                "name": meta["name"],
                "description": meta["description"],
                "frame_count": len(frame_files),
            })
        return result
