"""
Replicate Provider — calls Zero123++ via Replicate API for multi-view generation.
"""
import asyncio
import logging
import httpx
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# Zero123++ generates 6 views in a 3x2 grid (320x320 each):
#   Row 0: front-right(30°), front(0°), front-left(-30°)
#   Row 1: back-right(150°), back(180°), back-left(-150°)
# We extract: front (row0 col1), side (row0 col0), back (row1 col1)
VIEW_CROPS = {
    "front": (1, 0),  # col 1, row 0
    "side":  (0, 0),  # col 0, row 0 (front-right ≈ side)
    "back":  (1, 1),  # col 1, row 1
}
CELL_SIZE = 320


class ReplicateProvider:
    def __init__(self, api_token: str):
        self.api_token = api_token

    async def generate(self, image_path: str, output_dir: str) -> dict[str, str]:
        """
        Run Zero123++ on Replicate. Returns {"front": path, "side": path, "back": path}.
        """
        import replicate

        client = replicate.Client(api_token=self.api_token)

        # Run model in a thread (SDK is sync)
        output = await asyncio.to_thread(
            self._run_model, client, image_path
        )

        # output is a URL to the 3x2 grid image
        output_url = output if isinstance(output, str) else str(output)

        # Download the grid image
        async with httpx.AsyncClient() as http:
            resp = await http.get(output_url, timeout=60)
            resp.raise_for_status()

        grid_path = Path(output_dir) / "grid.png"
        grid_path.write_bytes(resp.content)

        # Crop individual views
        return await asyncio.to_thread(
            self._crop_views, str(grid_path), output_dir
        )

    def _run_model(self, client, image_path: str):
        with open(image_path, "rb") as f:
            output = client.run(
                "stability-ai/zero123plus",
                input={
                    "image": f,
                    "num_steps": 75,
                    "guidance_scale": 4.0,
                },
            )
        return output

    def _crop_views(self, grid_path: str, output_dir: str) -> dict[str, str]:
        grid = Image.open(grid_path)
        out = Path(output_dir)
        results = {}

        for view_name, (col, row) in VIEW_CROPS.items():
            x = col * CELL_SIZE
            y = row * CELL_SIZE
            crop = grid.crop((x, y, x + CELL_SIZE, y + CELL_SIZE))
            path = out / f"{view_name}.png"
            crop.save(str(path))
            results[view_name] = str(path)
            logger.info(f"Cropped view: {view_name} from grid ({col},{row}) → {path}")

        return results
