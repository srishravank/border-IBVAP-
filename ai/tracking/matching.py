import numpy as np
from typing import List, Tuple
from scipy.optimize import linear_sum_assignment


def bbox_ious(atlbrs: np.ndarray, btlbrs: np.ndarray) -> np.ndarray:
    """
    Compute IoU between two sets of bounding boxes [x1, y1, x2, y2].
    """
    ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    if atlbrs.size == 0 or btlbrs.size == 0:
        return ious

    atlbrs = np.ascontiguousarray(atlbrs, dtype=np.float32)
    btlbrs = np.ascontiguousarray(btlbrs, dtype=np.float32)

    for i, a in enumerate(atlbrs):
        for j, b in enumerate(btlbrs):
            x1 = max(a[0], b[0])
            y1 = max(a[1], b[1])
            x2 = min(a[2], b[2])
            y2 = min(a[3], b[3])
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            inter = w * h
            area_a = (a[2] - a[0]) * (a[3] - a[1])
            area_b = (b[2] - b[0]) * (b[3] - b[1])
            union = area_a + area_b - inter
            ious[i, j] = inter / union if union > 0 else 0.0

    return ious


def iou_distance(atracks: list, btracks: list) -> np.ndarray:
    """
    Computes IoU distance matrix between two lists of tracks / detections.
    Distance = 1.0 - IoU
    """
    if (len(atracks) > 0 and isinstance(atracks[0], np.ndarray)) or (len(btracks) > 0 and isinstance(btracks[0], np.ndarray)):
        atlbrs = atracks
        btlbrs = btracks
    else:
        atlbrs = [track.tlbr for track in atracks]
        btlbrs = [track.tlbr for track in btracks]

    _ious = bbox_ious(np.asarray(atlbrs, dtype=np.float32), np.asarray(btlbrs, dtype=np.float32))
    cost_matrix = 1.0 - _ious
    return cost_matrix


def linear_assignment(cost_matrix: np.ndarray, thresh: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Solves linear sum assignment problem with a distance threshold.
    Returns:
        matches: np.ndarray of shape (N, 2)
        unmatched_a: np.ndarray of unmatched indices in first list
        unmatched_b: np.ndarray of unmatched indices in second list
    """
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), np.arange(cost_matrix.shape[0]), np.arange(cost_matrix.shape[1])

    # Run SciPy Hungarian algorithm
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    matches, unmatched_a, unmatched_b = [], [], []
    for r, c in zip(row_ind, col_ind):
        if cost_matrix[r, c] <= thresh:
            matches.append([r, c])
        else:
            unmatched_a.append(r)
            unmatched_b.append(c)

    matched_rows = set(row_ind)
    matched_cols = set(col_ind)
    
    for i in range(cost_matrix.shape[0]):
        if i not in matched_rows:
            unmatched_a.append(i)
    for j in range(cost_matrix.shape[1]):
        if j not in matched_cols:
            unmatched_b.append(j)

    matches_arr = np.asarray(matches, dtype=int) if matches else np.empty((0, 2), dtype=int)
    unmatched_a_arr = np.asarray(unmatched_a, dtype=int)
    unmatched_b_arr = np.asarray(unmatched_b, dtype=int)

    return matches_arr, unmatched_a_arr, unmatched_b_arr
