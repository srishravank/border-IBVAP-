from typing import List, Tuple, Union
import cv2
import numpy as np


def get_reference_point(bbox: List[float], object_type: str = "person") -> Tuple[float, float]:
    """
    Computes ground-plane contact reference point from bounding box [x1, y1, x2, y2].
    For both persons and vehicles, bottom-center represents the ground contact point:
        cx = (x1 + x2) / 2.0
        ref_y = y2 (bottom edge)
    """
    x1, y1, x2, y2 = bbox
    cx = float((x1 + x2) / 2.0)
    ref_y = float(y2)
    return cx, ref_y


def point_in_polygon(point: Tuple[float, float], polygon: List[List[float]]) -> bool:
    """
    Determines whether a 2D point (x, y) lies strictly inside or on the boundary of a 2D polygon.
    Uses OpenCV pointPolygonTest with ray-casting mathematical fallback.
    """
    if len(polygon) < 3:
        return False

    px, py = float(point[0]), float(point[1])
    poly_pts = np.array(polygon, dtype=np.float32)

    # OpenCV pointPolygonTest: returns +ve (inside), 0 (on edge), -ve (outside)
    result = cv2.pointPolygonTest(poly_pts, (px, py), measureDist=False)
    return result >= 0


def ray_casting_point_in_polygon(x: float, y: float, polygon: List[List[float]]) -> bool:
    """
    Pure Python Ray-Casting algorithm for point-in-polygon verification.
    """
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def validate_polygon(polygon: List[List[float]]) -> Tuple[bool, str]:
    """
    Validates polygon coordinates:
    - At least 3 points
    - Points are valid numeric pairs
    - Non-zero area
    """
    if not isinstance(polygon, list) or len(polygon) < 3:
        return False, "Polygon must contain at least 3 vertex coordinates"

    for idx, pt in enumerate(polygon):
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            return False, f"Vertex #{idx} must be a coordinate pair [x, y]"
        try:
            float(pt[0]), float(pt[1])
        except (ValueError, TypeError):
            return False, f"Vertex #{idx} coordinates must be numeric"

    # Check non-degenerate polygon area
    pts = np.array(polygon, dtype=np.float32)
    area = cv2.contourArea(pts)
    if area < 1.0:
        return False, "Polygon vertex coordinates produce zero enclosed area"

    return True, "Valid"
