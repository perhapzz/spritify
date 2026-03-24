"""
Pose Detection Service - Uses TorchServe (for drawn characters) or MediaPipe (for photos)
"""
import cv2
import numpy as np
from pathlib import Path
import yaml
import logging
import requests
import os
from typing import Optional, Tuple
from PIL import Image
import io

logger = logging.getLogger(__name__)

# TorchServe URL (from environment or default)
TORCHSERVE_URL = os.environ.get("TORCHSERVE_URL", "http://localhost:8080")


class TorchServeDetector:
    """Uses TorchServe for drawn character detection (AnimatedDrawings official)"""

    def __init__(self, base_url: str = TORCHSERVE_URL):
        self.base_url = base_url
        self.detector_url = f"{base_url}/predictions/drawn_humanoid_detector"
        self.pose_url = f"{base_url}/predictions/drawn_humanoid_pose_estimator"

    def is_available(self) -> bool:
        """Check if TorchServe is running"""
        try:
            response = requests.get(f"{self.base_url}/ping", timeout=2)
            return response.status_code == 200
        except:
            return False

    def detect_bounding_box(self, image_path: str) -> Optional[dict]:
        """Detect character bounding box"""
        try:
            with open(image_path, 'rb') as f:
                response = requests.post(
                    self.detector_url,
                    files={'data': f},
                    timeout=30
                )
            if response.status_code == 200:
                return response.json()
            logger.warning(f"Detector returned {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Detector request failed: {e}")
            return None

    def detect_pose(self, image_path: str, bbox: dict) -> Optional[dict]:
        """Detect pose keypoints within bounding box"""
        try:
            # Load and crop image
            img = Image.open(image_path)

            # Crop to bounding box with padding
            left = max(0, bbox['left'])
            top = max(0, bbox['top'])
            right = min(img.width, bbox['right'])
            bottom = min(img.height, bbox['bottom'])

            cropped = img.crop((left, top, right, bottom))

            # Convert to bytes
            buf = io.BytesIO()
            cropped.save(buf, format='PNG')
            buf.seek(0)

            response = requests.post(
                self.pose_url,
                files={'data': buf},
                timeout=30
            )

            if response.status_code == 200:
                pose_data = response.json()
                # Adjust coordinates back to original image space
                for joint in pose_data.get('skeleton', []):
                    if 'loc' in joint:
                        joint['loc'][0] += left
                        joint['loc'][1] += top
                return pose_data
            logger.warning(f"Pose estimator returned {response.status_code}: {response.text}")
            return None
        except Exception as e:
            logger.error(f"Pose request failed: {e}")
            return None


class MediaPipeDetector:
    """Fallback detector using MediaPipe (better for real photos)"""

    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        base_options = python.BaseOptions(
            model_asset_path=self._get_model_path()
        )
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=True,
            running_mode=vision.RunningMode.IMAGE,
        )
        self.pose = vision.PoseLandmarker.create_from_options(options)
        self.mp = mp

    def _get_model_path(self) -> str:
        import urllib.request
        model_dir = Path(__file__).parent / "models"
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / "pose_landmarker_heavy.task"

        if not model_path.exists():
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
            logger.info(f"Downloading pose model from {url}")
            urllib.request.urlretrieve(url, model_path)

        return str(model_path)

    def detect(self, image: np.ndarray) -> Optional[np.ndarray]:
        h, w = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=image_rgb)

        results = self.pose.detect(mp_image)

        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            return None

        landmarks = results.pose_landmarks[0]
        self._last_segmentation = results.segmentation_masks[0] if results.segmentation_masks else None

        keypoints = np.zeros((17, 2))

        def get_coord(idx):
            return [landmarks[idx].x * w, landmarks[idx].y * h]

        keypoints[0] = get_coord(self.NOSE)
        keypoints[1] = keypoints[0]
        keypoints[2] = keypoints[0]
        keypoints[3] = keypoints[0]
        keypoints[4] = keypoints[0]
        keypoints[5] = get_coord(self.LEFT_SHOULDER)
        keypoints[6] = get_coord(self.RIGHT_SHOULDER)
        keypoints[7] = get_coord(self.LEFT_ELBOW)
        keypoints[8] = get_coord(self.RIGHT_ELBOW)
        keypoints[9] = get_coord(self.LEFT_WRIST)
        keypoints[10] = get_coord(self.RIGHT_WRIST)
        keypoints[11] = get_coord(self.LEFT_HIP)
        keypoints[12] = get_coord(self.RIGHT_HIP)
        keypoints[13] = get_coord(self.LEFT_KNEE)
        keypoints[14] = get_coord(self.RIGHT_KNEE)
        keypoints[15] = get_coord(self.LEFT_ANKLE)
        keypoints[16] = get_coord(self.RIGHT_ANKLE)

        return keypoints

    def get_segmentation_mask(self) -> Optional[np.ndarray]:
        if hasattr(self, '_last_segmentation') and self._last_segmentation is not None:
            mask_data = self._last_segmentation.numpy_view()
            return (mask_data * 255).astype(np.uint8)
        return None

    def close(self):
        if hasattr(self, 'pose'):
            self.pose.close()


def keypoints_to_skeleton(kpts: np.ndarray) -> list:
    """Convert MediaPipe keypoints to AnimatedDrawings skeleton format"""
    skeleton = [
        {'loc': [round(x) for x in (kpts[11] + kpts[12]) / 2], 'name': 'root', 'parent': None},
        {'loc': [round(x) for x in (kpts[11] + kpts[12]) / 2], 'name': 'hip', 'parent': 'root'},
        {'loc': [round(x) for x in (kpts[5] + kpts[6]) / 2], 'name': 'torso', 'parent': 'hip'},
        {'loc': [round(x) for x in kpts[0]], 'name': 'neck', 'parent': 'torso'},
        {'loc': [round(x) for x in kpts[6]], 'name': 'right_shoulder', 'parent': 'torso'},
        {'loc': [round(x) for x in kpts[8]], 'name': 'right_elbow', 'parent': 'right_shoulder'},
        {'loc': [round(x) for x in kpts[10]], 'name': 'right_hand', 'parent': 'right_elbow'},
        {'loc': [round(x) for x in kpts[5]], 'name': 'left_shoulder', 'parent': 'torso'},
        {'loc': [round(x) for x in kpts[7]], 'name': 'left_elbow', 'parent': 'left_shoulder'},
        {'loc': [round(x) for x in kpts[9]], 'name': 'left_hand', 'parent': 'left_elbow'},
        {'loc': [round(x) for x in kpts[12]], 'name': 'right_hip', 'parent': 'root'},
        {'loc': [round(x) for x in kpts[14]], 'name': 'right_knee', 'parent': 'right_hip'},
        {'loc': [round(x) for x in kpts[16]], 'name': 'right_foot', 'parent': 'right_knee'},
        {'loc': [round(x) for x in kpts[11]], 'name': 'left_hip', 'parent': 'root'},
        {'loc': [round(x) for x in kpts[13]], 'name': 'left_knee', 'parent': 'left_hip'},
        {'loc': [round(x) for x in kpts[15]], 'name': 'left_foot', 'parent': 'left_knee'},
    ]
    return skeleton


def segment_character(img: np.ndarray) -> np.ndarray:
    """Segment character from background using adaptive thresholding"""
    gray = np.min(img, axis=2)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 115, 8
    )
    thresh = cv2.bitwise_not(thresh)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_DILATE, kernel, iterations=2)

    h, w = thresh.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    mask[1:-1, 1:-1] = thresh.copy()

    im_floodfill = np.full(thresh.shape, 255, np.uint8)
    for x in range(0, w - 1, 10):
        cv2.floodFill(im_floodfill, mask, (x, 0), 0)
        cv2.floodFill(im_floodfill, mask, (x, h - 1), 0)
    for y in range(0, h - 1, 10):
        cv2.floodFill(im_floodfill, mask, (0, y), 0)
        cv2.floodFill(im_floodfill, mask, (w - 1, y), 0)

    im_floodfill[0, :] = 0
    im_floodfill[-1, :] = 0
    im_floodfill[:, 0] = 0
    im_floodfill[:, -1] = 0

    contours, _ = cv2.findContours(
        cv2.bitwise_not(im_floodfill),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return np.ones(thresh.shape, dtype=np.uint8) * 255

    largest = max(contours, key=cv2.contourArea)
    mask_result = np.zeros(thresh.shape, dtype=np.uint8)
    cv2.fillPoly(mask_result, [largest], 255)

    return mask_result


def create_character_annotations(
    image_path: str,
    output_dir: str,
) -> Tuple[bool, str]:
    """
    Create character annotation files from an image.
    Uses TorchServe for drawn characters, falls back to MediaPipe for photos.
    """
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True, parents=True)

    img = cv2.imread(image_path)
    if img is None:
        return False, f"Could not read image: {image_path}"

    h, w = img.shape[:2]
    cv2.imwrite(str(out_path / 'image.png'), img)

    # Resize if too large
    if max(img.shape) > 1000:
        scale = 1000 / max(img.shape)
        img = cv2.resize(img, (round(scale * w), round(scale * h)))
        h, w = img.shape[:2]

    skeleton = None
    mask = None

    # Try TorchServe first (better for drawn characters)
    torchserve = TorchServeDetector()
    if torchserve.is_available():
        logger.info("Using TorchServe for character detection")
        bbox = torchserve.detect_bounding_box(image_path)
        if bbox:
            pose_data = torchserve.detect_pose(image_path, bbox)
            if pose_data and 'skeleton' in pose_data:
                skeleton = pose_data['skeleton']
                logger.info(f"TorchServe detected {len(skeleton)} joints")

                # Create mask from bounding box
                mask = np.zeros((h, w), dtype=np.uint8)
                left = max(0, bbox.get('left', 0))
                top = max(0, bbox.get('top', 0))
                right = min(w, bbox.get('right', w))
                bottom = min(h, bbox.get('bottom', h))
                mask[top:bottom, left:right] = 255
    else:
        logger.info("TorchServe not available, trying MediaPipe")

    # Fallback to MediaPipe if TorchServe failed
    if skeleton is None:
        try:
            detector = MediaPipeDetector()
            keypoints = detector.detect(img)

            if keypoints is not None:
                skeleton = keypoints_to_skeleton(keypoints)
                mask = detector.get_segmentation_mask()
                logger.info("MediaPipe detected pose successfully")
            detector.close()
        except Exception as e:
            logger.warning(f"MediaPipe failed: {e}")

    # Still no skeleton - use example character
    if skeleton is None:
        return False, "Could not detect pose. TorchServe not running and MediaPipe failed."

    # Fallback mask
    if mask is None or np.sum(mask) < 1000:
        mask = segment_character(img)

    # Create character config
    char_cfg = {
        'skeleton': skeleton,
        'height': h,
        'width': w
    }

    # Save files
    texture = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    cv2.imwrite(str(out_path / 'texture.png'), texture)
    cv2.imwrite(str(out_path / 'mask.png'), mask)

    with open(str(out_path / 'char_cfg.yaml'), 'w') as f:
        yaml.dump(char_cfg, f)

    # Debug overlay
    overlay = texture.copy()
    for joint in skeleton:
        x, y = joint['loc']
        cv2.circle(overlay, (int(x), int(y)), 5, (0, 255, 0, 255), -1)
        cv2.putText(overlay, joint['name'], (int(x), int(y) + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255, 255), 1)
    cv2.imwrite(str(out_path / 'joint_overlay.png'), overlay)

    return True, "Character annotations created successfully"
