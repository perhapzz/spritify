"""
Pose Renderer — renders OpenPose keypoints as skeleton images for ControlNet input.
"""
from PIL import Image, ImageDraw

# OpenPose 18-keypoint skeleton connections
# Each tuple: (from_idx, to_idx)
SKELETON_PAIRS = [
    (0, 1),    # nose → neck
    (1, 2),    # neck → RShoulder
    (2, 3),    # RShoulder → RElbow
    (3, 4),    # RElbow → RWrist
    (1, 5),    # neck → LShoulder
    (5, 6),    # LShoulder → LElbow
    (6, 7),    # LElbow → LWrist
    (1, 8),    # neck → RHip
    (8, 9),    # RHip → RKnee
    (9, 10),   # RKnee → RAnkle
    (1, 11),   # neck → LHip
    (11, 12),  # LHip → LKnee
    (12, 13),  # LKnee → LAnkle
    (0, 14),   # nose → REye
    (0, 15),   # nose → LEye
    (14, 16),  # REye → REar
    (15, 17),  # LEye → LEar
]

# Colors per limb group (RGB)
LIMB_COLORS = {
    (0, 1): (255, 0, 0),
    (1, 2): (255, 85, 0), (2, 3): (255, 170, 0), (3, 4): (255, 255, 0),
    (1, 5): (170, 255, 0), (5, 6): (85, 255, 0), (6, 7): (0, 255, 0),
    (1, 8): (0, 255, 85), (8, 9): (0, 255, 170), (9, 10): (0, 255, 255),
    (1, 11): (0, 170, 255), (11, 12): (0, 85, 255), (12, 13): (0, 0, 255),
    (0, 14): (255, 0, 170), (0, 15): (170, 0, 255),
    (14, 16): (255, 0, 255), (15, 17): (85, 0, 255),
}


def render_pose_image(keypoints_2d: list, width: int = 256, height: int = 256) -> Image.Image:
    """
    Render OpenPose keypoints as a skeleton image (black background, colored lines).

    Args:
        keypoints_2d: flat list [x0,y0,c0, x1,y1,c1, ...] with coords in 0-1 range
        width, height: output image size
    Returns:
        PIL Image with skeleton drawn
    """
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Parse keypoints
    points = []
    for i in range(0, len(keypoints_2d), 3):
        x = keypoints_2d[i] * width
        y = keypoints_2d[i + 1] * height
        c = keypoints_2d[i + 2]
        points.append((x, y, c))

    # Draw skeleton lines
    for pair in SKELETON_PAIRS:
        idx_a, idx_b = pair
        if idx_a >= len(points) or idx_b >= len(points):
            continue
        xa, ya, ca = points[idx_a]
        xb, yb, cb = points[idx_b]
        if ca < 0.1 or cb < 0.1:
            continue
        color = LIMB_COLORS.get(pair, (255, 255, 255))
        draw.line([(xa, ya), (xb, yb)], fill=color, width=3)

    # Draw keypoint dots
    for x, y, c in points:
        if c < 0.1:
            continue
        r = 3
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255))

    return img
