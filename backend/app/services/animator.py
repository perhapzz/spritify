"""
Animator Service - Integrates with AnimatedDrawings to generate animation frames
"""
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
from PIL import Image
import yaml
import logging

from app.services.pose_detector import create_character_annotations

logger = logging.getLogger(__name__)

# Base path for AnimatedDrawings library
# __file__ = backend/app/services/animator.py
# We need: backend/../animated_drawings_lib = spritify/animated_drawings_lib
AD_LIB_PATH = Path(__file__).parent.parent.parent.parent / "animated_drawings_lib"

# Motion configurations
MOTION_CONFIGS = {
    "dab": {
        "bvh": "examples/bvh/fair1/dab.bvh",
        "start_frame": 0,
        "end_frame": 339,
        "retarget": "examples/config/retarget/fair1_ppf.yaml",
    },
    "jumping": {
        "bvh": "examples/bvh/fair1/jumping.bvh",
        "start_frame": 0,
        "end_frame": None,
        "retarget": "examples/config/retarget/fair1_ppf.yaml",
    },
    "wave_hello": {
        "bvh": "examples/bvh/fair1/wave_hello.bvh",
        "start_frame": 0,
        "end_frame": None,
        "retarget": "examples/config/retarget/fair1_ppf.yaml",
    },
    "zombie": {
        "bvh": "examples/bvh/fair1/zombie.bvh",
        "start_frame": 0,
        "end_frame": None,
        "retarget": "examples/config/retarget/fair1_ppf.yaml",
    },
    "jumping_jacks": {
        "bvh": "examples/bvh/cmu1/jumping_jacks.bvh",
        "start_frame": 0,
        "end_frame": None,
        "retarget": "examples/config/retarget/cmu1_bvh.yaml",
    },
    "jesse_dance": {
        "bvh": "examples/bvh/rokoko/jesse_dance.bvh",
        "start_frame": 0,
        "end_frame": None,
        "retarget": "examples/config/retarget/mixamo_fff.yaml",
    },
}


class AnimatorService:
    def __init__(self):
        self.ad_lib_path = AD_LIB_PATH
        self.temp_dirs: List[str] = []

    async def generate_frames(
        self,
        input_path: str,
        motion_id: str,
        frame_count: int = 8,
    ) -> List[Image.Image]:
        """
        Generate animation frames from a static image using AnimatedDrawings.
        """
        try:
            return await self._generate_with_animated_drawings(
                input_path, motion_id, frame_count
            )
        except Exception as e:
            logger.warning(f"AnimatedDrawings failed: {e}, falling back to placeholder")
            return await self._generate_placeholder_frames(input_path, frame_count)

    async def _generate_with_animated_drawings(
        self,
        input_path: str,
        motion_id: str,
        frame_count: int,
    ) -> List[Image.Image]:
        """
        Use AnimatedDrawings to generate animation frames.
        """
        import animated_drawings.render

        # Create temp directory for this generation
        temp_dir = tempfile.mkdtemp(prefix="spritify_")
        self.temp_dirs.append(temp_dir)
        char_dir = Path(temp_dir) / "character"

        try:
            # Step 1: Try to create character annotations using MediaPipe
            success, message = create_character_annotations(input_path, str(char_dir))

            if not success:
                # MediaPipe failed - use example character for demo
                # Copy texture from input but use example skeleton
                logger.warning(f"Pose detection failed: {message}")
                logger.info("Using example character skeleton for demo")

                # Use example character config
                example_char = self.ad_lib_path / "examples/characters/char1"
                char_cfg_src = example_char / "char_cfg.yaml"

                # Copy char_cfg but we'll use the uploaded image
                char_dir.mkdir(exist_ok=True, parents=True)
                import shutil
                shutil.copy(char_cfg_src, char_dir / "char_cfg.yaml")

                # Copy mask from example
                shutil.copy(example_char / "mask.png", char_dir / "mask.png")

                # Use uploaded image as texture (resize to match example dimensions)
                from PIL import Image
                import yaml

                with open(char_cfg_src, 'r') as f:
                    example_cfg = yaml.safe_load(f)

                target_h = example_cfg['height']
                target_w = example_cfg['width']

                # Resize input image to match example dimensions
                input_img = Image.open(input_path).convert("RGBA")
                input_img = input_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                input_img.save(str(char_dir / "texture.png"))

            # Step 2: Get motion configuration
            motion_config = MOTION_CONFIGS.get(motion_id)
            if not motion_config:
                # Default to dab if motion not found
                motion_config = MOTION_CONFIGS["dab"]
                logger.warning(f"Motion {motion_id} not found, using dab")

            # Step 3: Create motion config file
            motion_cfg_path = char_dir / "motion_cfg.yaml"
            bvh_path = self.ad_lib_path / motion_config["bvh"]

            motion_cfg = {
                "filepath": str(bvh_path),
                "start_frame_idx": motion_config["start_frame"],
                "groundplane_joint": "LeftFoot",
                "forward_perp_joint_vectors": [
                    ["LeftShoulder", "RightShoulder"],
                    ["LeftUpLeg", "RightUpLeg"],
                ],
                "scale": 0.025,
                "up": "+z",
            }
            if motion_config["end_frame"]:
                motion_cfg["end_frame_idx"] = motion_config["end_frame"]

            with open(motion_cfg_path, "w") as f:
                yaml.dump(motion_cfg, f)

            # Step 4: Create MVC config for rendering
            retarget_cfg_path = self.ad_lib_path / motion_config["retarget"]
            output_gif_path = char_dir / "video.gif"

            mvc_cfg = {
                "scene": {
                    "ANIMATED_CHARACTERS": [{
                        "character_cfg": str(char_dir / "char_cfg.yaml"),
                        "motion_cfg": str(motion_cfg_path),
                        "retarget_cfg": str(retarget_cfg_path),
                    }]
                },
                "controller": {
                    "MODE": "video_render",
                    "OUTPUT_VIDEO_PATH": str(output_gif_path),
                },
                # Note: Headless rendering with Mesa not available on macOS
                # Will use GLFW window (works but requires display)
            }

            mvc_cfg_path = char_dir / "mvc_cfg.yaml"
            with open(mvc_cfg_path, "w") as f:
                yaml.dump(mvc_cfg, f)

            # Step 5: Render animation
            animated_drawings.render.start(str(mvc_cfg_path))

            # Step 6: Extract frames from GIF
            if not output_gif_path.exists():
                raise FileNotFoundError(f"Animation output not found: {output_gif_path}")

            frames = await self._extract_frames_from_gif(
                str(output_gif_path),
                max_frames=frame_count
            )

            return frames

        except Exception as e:
            logger.error(f"Error generating animation: {e}")
            raise

    async def _extract_frames_from_gif(
        self,
        gif_path: str,
        max_frames: Optional[int] = None,
    ) -> List[Image.Image]:
        """Extract frames from an animated GIF."""
        frames = []
        with Image.open(gif_path) as gif:
            total_frames = gif.n_frames

            # Calculate frame step to get desired number of frames
            if max_frames and max_frames < total_frames:
                step = total_frames // max_frames
            else:
                step = 1
                max_frames = total_frames

            for i in range(0, total_frames, step):
                if len(frames) >= max_frames:
                    break
                gif.seek(i)
                frame = gif.copy().convert("RGBA")
                frames.append(frame)

        return frames

    async def _generate_placeholder_frames(
        self,
        input_path: str,
        frame_count: int,
    ) -> List[Image.Image]:
        """
        Generate placeholder frames for development/testing.
        Creates simple transformations of the input image.
        """
        original = Image.open(input_path).convert("RGBA")
        frames = []

        # Simple bounce animation as placeholder
        for i in range(frame_count):
            frame = original.copy()
            # Add slight vertical offset for bounce effect
            offset = int(10 * abs((i / frame_count * 2) - 1))

            # Create new image with offset
            new_frame = Image.new("RGBA", original.size, (0, 0, 0, 0))
            new_frame.paste(frame, (0, offset))
            frames.append(new_frame)

        return frames

    def get_available_motions(self) -> List[dict]:
        """List available motion presets"""
        return [
            {"id": "dab", "name": "Dab", "description": "Dab dance move"},
            {"id": "jumping", "name": "Jump", "description": "Jumping motion"},
            {"id": "wave_hello", "name": "Wave", "description": "Waving hello"},
            {"id": "zombie", "name": "Zombie", "description": "Zombie walk"},
            {"id": "jumping_jacks", "name": "Jumping Jacks", "description": "Jumping jacks exercise"},
            {"id": "jesse_dance", "name": "Dance", "description": "Dance routine"},
        ]

    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_dir}: {e}")
        self.temp_dirs.clear()
