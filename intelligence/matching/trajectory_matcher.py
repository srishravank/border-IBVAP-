import numpy as np
from typing import List, Tuple, Optional


class TrajectoryMatcher:
    """
    Evaluates trajectory heading and direction compatibility between camera exit and entrance.
    """

    def compute_heading_vector(self, trajectory: List[List[float]]) -> Optional[np.ndarray]:
        """
        Extracts dominant direction vector from the last N trajectory points.
        Returns normalized 2D vector [dx, dy] or None if stationary/insufficient trail.
        """
        if not trajectory or len(trajectory) < 2:
            return None

        # Take points across the trail (e.g. from first third to last point)
        pts = np.array(trajectory, dtype=np.float32)
        start_pt = pts[0]
        end_pt = pts[-1]

        diff = end_pt - start_pt
        norm = np.linalg.norm(diff)
        if norm < 5.0:  # Less than 5px movement (stationary)
            return None

        return diff / norm

    def evaluate_trajectory_compatibility(
        self,
        traj_a: List[List[float]],
        traj_b: List[List[float]],
        expected_direction: str = "forward"
    ) -> Tuple[float, str]:
        """
        Evaluates whether movement on camera A connects logically with movement on camera B.

        Returns:
            (score, reason)
        """
        vec_a = self.compute_heading_vector(traj_a)
        vec_b = self.compute_heading_vector(traj_b)

        if vec_a is None or vec_b is None:
            # Neutral compatibility if stationary or trajectory is short
            return 0.70, "Neutral trajectory compatibility (stationary or short trail)"

        # Dot product of headings
        dot = float(np.dot(vec_a, vec_b))

        if dot > 0.5:
            score = 0.90 + (0.10 * dot)
            reason = f"Consistent movement direction (vector dot product: {dot:.2f})"
        elif dot > 0.0:
            score = 0.75 + (0.15 * dot)
            reason = f"Moderately aligned movement heading (vector dot product: {dot:.2f})"
        else:
            score = max(0.30, 0.60 + (0.30 * dot))
            reason = f"Divergent movement heading (vector dot product: {dot:.2f})"

        return round(score, 3), reason
