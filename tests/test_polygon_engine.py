import pytest
from verification.polygon_engine import (
    point_in_polygon,
    ray_casting_point_in_polygon,
    get_reference_point,
    validate_polygon
)


def test_point_in_polygon_inside_and_outside():
    """Test: Accurately determines if reference point is strictly inside or outside a polygon."""
    # Rectangle polygon: (100, 100) to (500, 400)
    polygon = [[100.0, 100.0], [500.0, 100.0], [500.0, 400.0], [100.0, 400.0]]

    # Point clearly inside
    inside_pt = (300.0, 250.0)
    assert point_in_polygon(inside_pt, polygon) is True
    assert ray_casting_point_in_polygon(300.0, 250.0, polygon) is True

    # Point clearly outside
    outside_pt = (50.0, 50.0)
    assert point_in_polygon(outside_pt, polygon) is False
    assert ray_casting_point_in_polygon(50.0, 50.0, polygon) is False

    # Point just outside right boundary
    outside_right = (550.0, 250.0)
    assert point_in_polygon(outside_right, polygon) is False


def test_get_reference_point_ground_contact():
    """Test: Reference point correctly computes bottom-center contact point."""
    bbox = [100.0, 80.0, 200.0, 300.0]  # x1=100, y1=80, x2=200, y2=300
    ref_x, ref_y = get_reference_point(bbox, object_type="person")

    assert ref_x == 150.0  # (100 + 200) / 2
    assert ref_y == 300.0  # y2 bottom edge


def test_validate_polygon_validation_rules():
    """Test: Geometry validator rejects degenerate or corrupt polygon inputs."""
    # Valid polygon (triangle)
    valid_poly = [[0.0, 0.0], [100.0, 0.0], [50.0, 100.0]]
    is_valid, msg = validate_polygon(valid_poly)
    assert is_valid is True

    # Too few points (< 3)
    invalid_few = [[0.0, 0.0], [100.0, 100.0]]
    is_valid, msg = validate_polygon(invalid_few)
    assert is_valid is False
    assert "at least 3" in msg

    # Degenerate zero area (collinear points)
    degenerate = [[0.0, 0.0], [50.0, 0.0], [100.0, 0.0]]
    is_valid, msg = validate_polygon(degenerate)
    assert is_valid is False
