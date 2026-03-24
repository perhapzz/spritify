"""Generate OpenPose 18-keypoint JSON sequences for walk/run/idle/jump."""
import json, math, os

# Keypoint indices: 0=nose,1=neck,2=RShoulder,3=RElbow,4=RWrist,
# 5=LShoulder,6=LElbow,7=LWrist,8=RHip,9=RKnee,10=RAnkle,
# 11=LHip,12=LKnee,13=LAnkle,14=REye,15=LEye,16=REar,17=LEar

# All coords normalized to 0-1 range (256x256 canvas)
# c=confidence, always 1.0 for synthetic data

def kp(x, y, c=1.0):
    return [round(x, 4), round(y, 4), c]

def make_frame(points_18):
    flat = []
    for p in points_18:
        flat.extend(p)
    return {"people": [{"pose_keypoints_2d": flat}]}

def lerp(a, b, t):
    return [a[i] + (b[i] - a[i]) * t for i in range(len(a))]

# Base standing pose (front view)
BASE = [
    kp(0.5, 0.12),   # 0 nose
    kp(0.5, 0.20),   # 1 neck
    kp(0.42, 0.20),  # 2 RShoulder
    kp(0.38, 0.32),  # 3 RElbow
    kp(0.36, 0.42),  # 4 RWrist
    kp(0.58, 0.20),  # 5 LShoulder
    kp(0.62, 0.32),  # 6 LElbow
    kp(0.64, 0.42),  # 7 LWrist
    kp(0.45, 0.45),  # 8 RHip
    kp(0.45, 0.62),  # 9 RKnee
    kp(0.45, 0.80),  # 10 RAnkle
    kp(0.55, 0.45),  # 11 LHip
    kp(0.55, 0.62),  # 12 LKnee
    kp(0.55, 0.80),  # 13 LAnkle
    kp(0.47, 0.10),  # 14 REye
    kp(0.53, 0.10),  # 15 LEye
    kp(0.44, 0.11),  # 16 REar
    kp(0.56, 0.11),  # 17 LEar
]

def offset_pose(base, deltas):
    """Apply (dx, dy) deltas to base pose."""
    result = []
    for i, p in enumerate(base):
        dx, dy = deltas.get(i, (0, 0))
        result.append(kp(p[0] + dx, p[1] + dy))
    return result

def sin_cycle(frame, total, amplitude, phase=0):
    return amplitude * math.sin(2 * math.pi * frame / total + phase)

def write_sequence(name, frames):
    d = f"pose_data/{name}"
    for i, f in enumerate(frames):
        with open(f"{d}/frame_{i}.json", "w") as fp:
            json.dump(f, fp, indent=2)
    print(f"  {name}: {len(frames)} frames")

# === WALK (8 frames) ===
walk_frames = []
for i in range(8):
    t = i / 8
    angle = 2 * math.pi * t
    # Leg swing
    r_knee_dx = sin_cycle(i, 8, 0.03)
    r_ankle_dx = sin_cycle(i, 8, 0.05)
    l_knee_dx = sin_cycle(i, 8, 0.03, math.pi)
    l_ankle_dx = sin_cycle(i, 8, 0.05, math.pi)
    # Arm swing (opposite to legs)
    r_elbow_dx = sin_cycle(i, 8, 0.02, math.pi)
    r_wrist_dx = sin_cycle(i, 8, 0.03, math.pi)
    l_elbow_dx = sin_cycle(i, 8, 0.02)
    l_wrist_dx = sin_cycle(i, 8, 0.03)
    # Body bob
    body_dy = abs(sin_cycle(i, 8, 0.01))
    
    deltas = {
        0: (0, body_dy), 1: (0, body_dy),
        3: (r_elbow_dx, body_dy), 4: (r_wrist_dx, body_dy),
        6: (l_elbow_dx, body_dy), 7: (l_wrist_dx, body_dy),
        9: (r_knee_dx, body_dy), 10: (r_ankle_dx, body_dy),
        12: (l_knee_dx, body_dy), 13: (l_ankle_dx, body_dy),
        14: (0, body_dy), 15: (0, body_dy), 16: (0, body_dy), 17: (0, body_dy),
    }
    walk_frames.append(make_frame(offset_pose(BASE, deltas)))

# === RUN (8 frames) ===
run_frames = []
for i in range(8):
    # Wider swing, more knee lift
    r_knee_dx = sin_cycle(i, 8, 0.05)
    r_knee_dy = -abs(sin_cycle(i, 8, 0.06))
    r_ankle_dx = sin_cycle(i, 8, 0.08)
    r_ankle_dy = -abs(sin_cycle(i, 8, 0.04))
    l_knee_dx = sin_cycle(i, 8, 0.05, math.pi)
    l_knee_dy = -abs(sin_cycle(i, 8, 0.06, math.pi))
    l_ankle_dx = sin_cycle(i, 8, 0.08, math.pi)
    l_ankle_dy = -abs(sin_cycle(i, 8, 0.04, math.pi))
    r_elbow_dx = sin_cycle(i, 8, 0.04, math.pi)
    l_elbow_dx = sin_cycle(i, 8, 0.04)
    body_dy = abs(sin_cycle(i, 8, 0.02))
    
    deltas = {
        0: (0, body_dy), 1: (0, body_dy),
        3: (r_elbow_dx, body_dy - 0.02), 4: (r_elbow_dx * 1.3, body_dy - 0.03),
        6: (l_elbow_dx, body_dy - 0.02), 7: (l_elbow_dx * 1.3, body_dy - 0.03),
        9: (r_knee_dx, r_knee_dy + body_dy), 10: (r_ankle_dx, r_ankle_dy + body_dy),
        12: (l_knee_dx, l_knee_dy + body_dy), 13: (l_ankle_dx, l_ankle_dy + body_dy),
        14: (0, body_dy), 15: (0, body_dy), 16: (0, body_dy), 17: (0, body_dy),
    }
    run_frames.append(make_frame(offset_pose(BASE, deltas)))

# === IDLE (4 frames — subtle breathing) ===
idle_frames = []
for i in range(4):
    breath = sin_cycle(i, 4, 0.005)
    deltas = {
        2: (breath, 0), 5: (-breath, 0),  # shoulders expand/contract
        0: (0, -breath), 14: (0, -breath), 15: (0, -breath),
    }
    idle_frames.append(make_frame(offset_pose(BASE, deltas)))

# === JUMP (8 frames) ===
# Crouch → launch → air → peak → descend → land → recover → stand
jump_offsets = [
    # frame 0: crouch
    {9: (0, 0.04), 10: (0, 0.06), 12: (0, 0.04), 13: (0, 0.06),
     0: (0, 0.03), 1: (0, 0.03), 3: (0, 0.03), 4: (0, 0.03), 6: (0, 0.03), 7: (0, 0.03)},
    # frame 1: launch
    {0: (0, -0.02), 1: (0, -0.02), 3: (-0.02, -0.04), 4: (-0.03, -0.06),
     6: (0.02, -0.04), 7: (0.03, -0.06)},
    # frame 2: rising
    {0: (0, -0.08), 1: (0, -0.08), 2: (0, -0.08), 5: (0, -0.08),
     3: (-0.03, -0.12), 4: (-0.04, -0.15), 6: (0.03, -0.12), 7: (0.04, -0.15),
     8: (0, -0.08), 11: (0, -0.08), 9: (0.02, -0.06), 10: (0.03, -0.04),
     12: (-0.02, -0.06), 13: (-0.03, -0.04),
     14: (0, -0.08), 15: (0, -0.08), 16: (0, -0.08), 17: (0, -0.08)},
    # frame 3: peak
    {0: (0, -0.12), 1: (0, -0.12), 2: (0, -0.12), 5: (0, -0.12),
     3: (-0.02, -0.14), 4: (-0.02, -0.13), 6: (0.02, -0.14), 7: (0.02, -0.13),
     8: (0, -0.12), 11: (0, -0.12), 9: (0.02, -0.10), 10: (0.03, -0.08),
     12: (-0.02, -0.10), 13: (-0.03, -0.08),
     14: (0, -0.12), 15: (0, -0.12), 16: (0, -0.12), 17: (0, -0.12)},
    # frame 4: descending
    {0: (0, -0.08), 1: (0, -0.08), 2: (0, -0.08), 5: (0, -0.08),
     3: (-0.01, -0.10), 4: (-0.01, -0.09), 6: (0.01, -0.10), 7: (0.01, -0.09),
     8: (0, -0.08), 11: (0, -0.08), 9: (0, -0.06), 10: (0, -0.04),
     12: (0, -0.06), 13: (0, -0.04),
     14: (0, -0.08), 15: (0, -0.08), 16: (0, -0.08), 17: (0, -0.08)},
    # frame 5: landing
    {9: (0, 0.03), 10: (0, 0.05), 12: (0, 0.03), 13: (0, 0.05),
     0: (0, 0.02), 1: (0, 0.02)},
    # frame 6: recover
    {9: (0, 0.01), 10: (0, 0.02), 12: (0, 0.01), 13: (0, 0.02)},
    # frame 7: stand (back to base)
    {},
]
jump_frames = [make_frame(offset_pose(BASE, d)) for d in jump_offsets]

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__))))

print("Generating pose sequences...")
write_sequence("walk", walk_frames)
write_sequence("run", run_frames)
write_sequence("idle", idle_frames)
write_sequence("jump", jump_frames)
print("Done!")
