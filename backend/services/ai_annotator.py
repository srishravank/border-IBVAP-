import cv2
import numpy as np
from typing import List, Optional, Tuple, Any, Dict
from backend.models.track import TrackedObject
from backend.models.detection import DetectionResult
from backend.models.zone import ZoneResponse

# Category colors (BGR format)
COLOR_PERSON = (40, 210, 120)    # Emerald Green
COLOR_CAR = (230, 180, 20)       # Cyan / Light Blue
COLOR_HEAVY = (30, 140, 245)     # Amber / Orange for truck & bus
COLOR_BIKE = (200, 70, 180)      # Purple for motorcycle & bike
COLOR_ANIMAL = (50, 180, 240)    # Amber / Gold for animals
COLOR_OBJECT = (220, 100, 240)   # Pink for luggage/bags
COLOR_DEFAULT = (200, 200, 200)


def hex_to_bgr(hex_str: str) -> Tuple[int, int, int]:
    """Converts hex color (#RRGGBB) to OpenCV BGR tuple."""
    try:
        hex_clean = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
        return (b, g, r)
    except Exception:
        return (244, 63, 94)  # Default rose red


def get_category_color(obj_type: str, subclass: Optional[str] = None) -> Tuple[int, int, int]:
    if obj_type == "person":
        return COLOR_PERSON
    if obj_type == "animal":
        return COLOR_ANIMAL
    if obj_type == "object":
        return COLOR_OBJECT
    if subclass in ("truck", "bus", "train"):
        return COLOR_HEAVY
    if subclass in ("motorcycle", "bicycle"):
        return COLOR_BIKE
    return COLOR_CAR


def annotate_frame(
    frame: np.ndarray,
    tracks: List[TrackedObject],
    detections: Optional[List[DetectionResult]] = None,
    zones: Optional[List[ZoneResponse]] = None,
    active_candidates: Optional[List[Dict[str, Any]]] = None,
    fps: float = 0.0,
    inference_ms: float = 0.0,
    model_name: str = "YOLO"
) -> np.ndarray:
    """
    Renders AI visual overlays on the frame:
    - Virtual fence polygons with semi-transparent shading and tactical headers
    - Bounding boxes and persistent ID badges (e.g. 'PERSON P001 [0.94]')
    - Trajectory motion trails
    - Live verification candidate progress indicators (e.g. 'VERIFYING 2/3')
    - Tactical HUD telemetry
    """
    if frame is None or frame.size == 0:
        return frame

    vis_frame = frame.copy()
    h, w = vis_frame.shape[:2]

    # 1. Draw Virtual Fence Polygons (with semi-transparent shaded area)
    if zones:
        overlay = vis_frame.copy()
        for zone in zones:
            if not zone.enabled or len(zone.polygon) < 3:
                continue
            
            pts = np.array(zone.polygon, dtype=np.int32)
            color = hex_to_bgr(zone.color or "#F43F5E")
            
            # Fill polygon on overlay
            cv2.fillPoly(overlay, [pts], color)
            # Outline on main frame
            cv2.polylines(vis_frame, [pts], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_AA)

            # Zone Name Tag
            label = f"[VIRTUAL FENCE: {zone.zone_name.upper()}]"
            font = cv2.FONT_HERSHEY_SIMPLEX
            (lw, lh), _ = cv2.getTextSize(label, font, 0.4, 1)
            top_pt = zone.polygon[0]
            tx, ty = int(top_pt[0]), max(15, int(top_pt[1]) - 6)
            
            cv2.rectangle(vis_frame, (tx, ty - lh - 4), (tx + lw + 8, ty + 4), (15, 20, 25), -1)
            cv2.rectangle(vis_frame, (tx, ty - lh - 4), (tx + lw + 8, ty + 4), color, 1)
            cv2.putText(vis_frame, label, (tx + 4, ty - 2), font, 0.4, color, 1, cv2.LINE_AA)

        # Blend semi-transparent shading (alpha = 0.15)
        cv2.addWeighted(overlay, 0.15, vis_frame, 0.85, 0, vis_frame)

    # 2. Draw Trajectory Trails for Active Tracks
    for track in tracks:
        color = get_category_color(track.object_type, track.subclass)
        points = track.trajectory
        if len(points) > 1:
            for i in range(1, len(points)):
                pt1 = (int(points[i - 1][0]), int(points[i - 1][1]))
                pt2 = (int(points[i][0]), int(points[i][1]))
                thickness = 1 if i < len(points) // 2 else 2
                cv2.line(vis_frame, pt1, pt2, color, thickness, cv2.LINE_AA)
            # Latest point dot
            last_pt = (int(points[-1][0]), int(points[-1][1]))
            cv2.circle(vis_frame, last_pt, 4, color, -1, cv2.LINE_AA)

    # 3. Draw Track Bounding Boxes, Ground Reference Point, and Badges
    for track in tracks:
        color = get_category_color(track.object_type, track.subclass)
        x1, y1, x2, y2 = [int(v) for v in track.bbox]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        # Draw Bounding Box
        cv2.rectangle(vis_frame, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

        # Draw Ground Reference Point (Bottom-Center)
        cx, ref_y = int((x1 + x2) / 2.0), y2
        cv2.circle(vis_frame, (cx, ref_y), 4, (0, 255, 255), -1, cv2.LINE_AA)

        # Top-corner reticles for tactical border UI
        ret_len = min(15, (x2 - x1) // 4, (y2 - y1) // 4)
        if ret_len > 3:
            cv2.line(vis_frame, (x1, y1), (x1 + ret_len, y1), (255, 255, 255), 2)
            cv2.line(vis_frame, (x1, y1), (x1, y1 + ret_len), (255, 255, 255), 2)
            cv2.line(vis_frame, (x2, y2), (x2 - ret_len, y2), (255, 255, 255), 2)
            cv2.line(vis_frame, (x2, y2), (x2, y2 - ret_len), (255, 255, 255), 2)

        # Label Pill: [OBJECT_TYPE ID | CONF]
        label = f"{track.class_name.upper()} {track.formatted_id} [{track.confidence:.2f}]"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.45
        font_thick = 1
        (label_w, label_h), _ = cv2.getTextSize(label, font, font_scale, font_thick)

        # Draw label background
        badge_y1 = max(0, y1 - label_h - 8)
        badge_y2 = badge_y1 + label_h + 8
        badge_x2 = min(w, x1 + label_w + 10)
        cv2.rectangle(vis_frame, (x1, badge_y1), (badge_x2, badge_y2), color, -1)
        cv2.putText(
            vis_frame,
            label,
            (x1 + 5, badge_y2 - 5),
            font,
            font_scale,
            (10, 15, 20),
            font_thick,
            cv2.LINE_AA
        )

    # 4. Draw Live Verification Gate Candidates Banner (Top Center)
    if active_candidates:
        cand_y = 65
        for cand in active_candidates:
            cand_text = f"🚨 {cand['formatted_track_id']} INTRUSION: {cand['status']} ({cand['confirmed_frames']}/{cand['required_frames']} FRAMES)"
            font = cv2.FONT_HERSHEY_SIMPLEX
            (cw, ch), _ = cv2.getTextSize(cand_text, font, 0.45, 1)
            cx_pos = max(10, (w - cw) // 2)
            
            # Flashing amber/red badge
            cv2.rectangle(vis_frame, (cx_pos - 10, cand_y - ch - 6), (cx_pos + cw + 10, cand_y + 6), (20, 20, 30), -1)
            cv2.rectangle(vis_frame, (cx_pos - 10, cand_y - ch - 6), (cx_pos + cw + 10, cand_y + 6), (0, 165, 255), 2)
            cv2.putText(vis_frame, cand_text, (cx_pos, cand_y), font, 0.45, (0, 220, 255), 1, cv2.LINE_AA)
            cand_y += 30

    # 5. Tactical HUD Telemetry in Bottom Left Corner
    hud_bg_w = 300
    hud_bg_h = 45
    cv2.rectangle(vis_frame, (10, h - hud_bg_h - 10), (10 + hud_bg_w, h - 10), (15, 20, 25), -1)
    cv2.rectangle(vis_frame, (10, h - hud_bg_h - 10), (10 + hud_bg_w, h - 10), (45, 60, 80), 1)

    hud_text1 = f"AI: {model_name} | Latency: {inference_ms:.1f}ms"
    hud_text2 = f"Active Tracks: {len(tracks)} | Zones: {len(zones or [])} | FPS: {fps:.1f}"
    cv2.putText(vis_frame, hud_text1, (18, h - hud_bg_h + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(vis_frame, hud_text2, (18, h - hud_bg_h + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 220, 200), 1, cv2.LINE_AA)

    return vis_frame
