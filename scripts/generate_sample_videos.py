import os
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

def create_synthetic_cctv_video(
    output_path: str,
    sector_name: str,
    cam_id: str,
    duration_sec: int = 10,
    fps: int = 25,
    width: int = 1280,
    height: int = 720,
    scene_type: str = "gate"
):
    """Generates an authentic CCTV simulation video with moving elements, OSD timestamp, and grid lines."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Use MP4V codec which is universally supported across OpenCV installations
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    total_frames = duration_sec * fps
    
    for frame_idx in range(total_frames):
        # Base background - simulated camera sensor background with slight noise
        if scene_type == "gate":
            # Dark asphalt / road gate scene
            frame = np.full((height, width, 3), (35, 40, 38), dtype=np.uint8)
            # Road markings
            cv2.line(frame, (width // 2, 200), (width // 2, height), (80, 80, 80), 4)
            # Barrier / Gate post
            cv2.rectangle(frame, (100, 300), (160, height), (60, 60, 100), -1)
            cv2.rectangle(frame, (width - 160, 300), (width - 100, height), (60, 60, 100), -1)
            # Moving simulated vehicle / box
            pos_y = int(250 + (frame_idx % (fps * 5)) * ((height - 350) / (fps * 5)))
            cv2.rectangle(frame, (width // 2 - 80, pos_y), (width // 2 + 80, pos_y + 120), (50, 120, 160), -1)
            cv2.putText(frame, "SIM-VEHICLE-01", (width // 2 - 70, pos_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        elif scene_type == "perimeter":
            # Desert / grass perimeter fence
            frame = np.full((height, width, 3), (30, 45, 50), dtype=np.uint8)
            # Wire fence line diagonals
            for x in range(0, width, 60):
                cv2.line(frame, (x, 250), (x + 30, height), (70, 75, 70), 2)
            cv2.line(frame, (0, 350), (width, 350), (100, 100, 100), 3)
            cv2.line(frame, (0, 500), (width, 500), (100, 100, 100), 3)
            # Moving patrol target
            pos_x = int((frame_idx % (fps * 6)) * (width / (fps * 6)))
            cv2.circle(frame, (pos_x, 420), 25, (80, 180, 90), -1)
            cv2.putText(frame, "PATROL-UNIT", (pos_x - 45, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 255, 200), 1)

        elif scene_type == "riverine":
            # Night vision / IR low-light river scene
            frame = np.full((height, width, 3), (25, 30, 25), dtype=np.uint8)
            # Water wave lines
            t = frame_idx * 0.1
            for y in range(300, height, 40):
                offset = int(np.sin(t + y * 0.05) * 20)
                cv2.line(frame, (0, y + offset), (width, y - offset), (45, 60, 45), 2)
            # Moving vessel / raft simulator
            pos_x = int(width - (frame_idx % (fps * 7)) * (width / (fps * 7)))
            cv2.ellipse(frame, (pos_x, 480), (70, 25), 0, 0, 360, (70, 100, 70), -1)
            cv2.putText(frame, "VESSEL-IR", (pos_x - 35, 485), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 220, 180), 1)

        else:  # Watchtower
            frame = np.full((height, width, 3), (35, 30, 40), dtype=np.uint8)
            # Crosshair & panoramic grid
            cv2.circle(frame, (width // 2, height // 2), 220, (60, 60, 80), 1)
            cv2.circle(frame, (width // 2, height // 2), 110, (60, 60, 80), 1)
            cv2.line(frame, (width // 2 - 250, height // 2), (width // 2 + 250, height // 2), (60, 60, 80), 1)
            cv2.line(frame, (width // 2, height // 2 - 250), (width // 2, height // 2 + 250), (60, 60, 80), 1)
            # Rotating radar sweep
            angle = (frame_idx * 6) % 360
            rad = np.deg2rad(angle)
            end_x = int(width // 2 + 220 * np.cos(rad))
            end_y = int(height // 2 + 220 * np.sin(rad))
            cv2.line(frame, (width // 2, height // 2), (end_x, end_y), (120, 90, 180), 2)

        # Subtle noise overlay
        noise = np.random.randint(0, 15, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)

        # CCTV On-Screen Display (OSD) Header
        cv2.rectangle(frame, (0, 0), (width, 50), (15, 15, 15), -1)
        cv2.putText(frame, f"IBVAP 2.0 EDGE FEED | {cam_id} | {sector_name}", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2)
        
        # Frame counter & UTC timestamp OSD
        ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(frame, f"REC [LIVE]  {ts_str} UTC  F:{frame_idx:05d}", (width - 460, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

        # CCTV Reticle corners
        reticle_color = (0, 200, 150)
        cv2.line(frame, (30, 80), (70, 80), reticle_color, 2)
        cv2.line(frame, (30, 80), (30, 120), reticle_color, 2)
        cv2.line(frame, (width - 30, 80), (width - 70, 80), reticle_color, 2)
        cv2.line(frame, (width - 30, 80), (width - 30, 120), reticle_color, 2)
        cv2.line(frame, (30, height - 30), (70, height - 30), reticle_color, 2)
        cv2.line(frame, (30, height - 30), (30, height - 70), reticle_color, 2)
        cv2.line(frame, (width - 30, height - 30), (width - 70, height - 30), reticle_color, 2)
        cv2.line(frame, (width - 30, height - 30), (width - 30, height - 70), reticle_color, 2)

        out.write(frame)

    out.release()
    print(f"Generated {output_path} ({duration_sec}s @ {fps}fps, {width}x{height})")


def main():
    base_dir = Path(__file__).resolve().parent.parent
    video_dir = base_dir / "data" / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    cameras = [
        ("camera01.mp4", "Sector A - Main Border Gate", "CAM-01", "gate"),
        ("camera02.mp4", "Sector B - Perimeter Fence Alpha", "CAM-02", "perimeter"),
        ("camera03.mp4", "Sector C - Riverine Border Crossing", "CAM-03", "riverine"),
        ("camera04.mp4", "Sector D - Outpost Watchtower", "CAM-04", "watchtower"),
    ]

    for filename, sector, cam_id, scene in cameras:
        out_file = str(video_dir / filename)
        create_synthetic_cctv_video(
            output_path=out_file,
            sector_name=sector,
            cam_id=cam_id,
            duration_sec=8,
            fps=25,
            width=1280,
            height=720,
            scene_type=scene
        )

if __name__ == "__main__":
    main()
