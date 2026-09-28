from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class CameraRelation:
    relation_id: str
    source_camera: str
    destination_camera: str
    min_transition_seconds: float = 5.0
    max_transition_seconds: float = 180.0
    distance_meters: float = 50.0
    direction: str = "bidirectional"
    enabled: bool = True
    description: str = ""


class CameraTopologyGraph:
    """
    In-memory graph representing inter-camera physical and logical adjacency relationships.
    Used to filter candidate track comparisons and enforce spatial route validity.
    """

    def __init__(self):
        # Key: (source, destination) -> CameraRelation
        self.relations: Dict[Tuple[str, str], CameraRelation] = {}
        self.adjacency: Dict[str, Set[str]] = {}

    def clear(self):
        self.relations.clear()
        self.adjacency.clear()

    def add_relation(self, relation: CameraRelation):
        if not relation.enabled:
            return

        src, dst = relation.source_camera, relation.destination_camera
        self.relations[(src, dst)] = relation
        self.adjacency.setdefault(src, set()).add(dst)

        if relation.direction == "bidirectional":
            reverse_rel = CameraRelation(
                relation_id=f"{relation.relation_id}-REV",
                source_camera=dst,
                destination_camera=src,
                min_transition_seconds=relation.min_transition_seconds,
                max_transition_seconds=relation.max_transition_seconds,
                distance_meters=relation.distance_meters,
                direction="bidirectional",
                enabled=True,
                description=relation.description
            )
            self.relations[(dst, src)] = reverse_rel
            self.adjacency.setdefault(dst, set()).add(src)

    def is_connected(self, source_cam: str, dest_cam: str) -> bool:
        """Returns True if there is a direct enabled topology link between source and destination."""
        if source_cam == dest_cam:
            return True
        return (source_cam, dest_cam) in self.relations

    def get_relation(self, source_cam: str, dest_cam: str) -> Optional[CameraRelation]:
        """Gets direct relation between two cameras."""
        return self.relations.get((source_cam, dest_cam))

    def get_connected_cameras(self, camera_id: str) -> List[str]:
        """Returns all directly connected neighbor cameras."""
        return list(self.adjacency.get(camera_id, set()))

    def get_candidate_ancestors(self, current_camera: str) -> List[str]:
        """Returns cameras that could have transitioned into the current camera."""
        ancestors = []
        for (src, dst), rel in self.relations.items():
            if dst == current_camera and rel.enabled:
                ancestors.append(src)
        return list(set(ancestors))
