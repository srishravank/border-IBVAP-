import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.database.connection import SessionLocal
from backend.database.models import (
    SubjectModel,
    SubjectTrackLinkModel,
    IncidentModel,
    IncidentEventLinkModel,
    SecurityEventModel,
    AssociatedVehicleModel,
    CameraModel
)
from intelligence.graph.graph_models import GraphNode, GraphEdge, IncidentGraph

logger = logging.getLogger("ibvap.graph")


class IncidentGraphBuilder:
    """
    Builds structured node-edge Incident Graphs from actual database models
    representing subjects, camera observations, zone events, and associated vehicles.
    """

    @staticmethod
    def build_graph_for_subject(subject_id: str, incident_id: Optional[str] = None) -> IncidentGraph:
        db = SessionLocal()
        try:
            subject = db.query(SubjectModel).filter(SubjectModel.subject_id == subject_id).first()
            if not subject:
                return IncidentGraph(
                    incident_id=incident_id or f"INC-{subject_id}",
                    subject_id=subject_id,
                    nodes=[],
                    edges=[],
                    generated_at=datetime.now(timezone.utc).isoformat()
                )

            inc_id = incident_id or f"INC-{subject_id}"

            nodes_dict: Dict[str, GraphNode] = {}
            edges: List[GraphEdge] = []
            edge_ids_seen = set()

            def add_node(node: GraphNode):
                if node.node_id not in nodes_dict:
                    nodes_dict[node.node_id] = node

            def add_edge(edge: GraphEdge):
                if edge.edge_id not in edge_ids_seen:
                    edges.append(edge)
                    edge_ids_seen.add(edge.edge_id)

            # 1. Primary Subject Node
            subj_label = f"{subject.subject_id} ({subject.object_type.upper()})"
            add_node(GraphNode(
                node_id=subject.subject_id,
                node_type="SUBJECT",
                label=subj_label,
                reference_id=subject.subject_id,
                properties={
                    "object_type": subject.object_type,
                    "first_seen": subject.first_seen.isoformat(),
                    "last_seen": subject.last_seen.isoformat(),
                    "status": subject.status,
                    "total_cameras": subject.total_cameras_visited
                }
            ))

            # 2. Track Links & Camera Nodes
            links = db.query(SubjectTrackLinkModel).filter(
                SubjectTrackLinkModel.subject_id == subject_id
            ).order_by(SubjectTrackLinkModel.first_timestamp.asc()).all()

            prev_cam_id = None
            prev_track_node_id = None

            for link in links:
                cam_id = link.camera_id
                cam_node_id = f"NODE-{cam_id}"
                track_node_id = f"NODE-{cam_id}-TRK{link.track_id}"

                # Camera Node
                add_node(GraphNode(
                    node_id=cam_node_id,
                    node_type="CAMERA",
                    label=f"Camera {cam_id}",
                    reference_id=cam_id,
                    properties={"camera_id": cam_id}
                ))

                # Local Track Node
                add_node(GraphNode(
                    node_id=track_node_id,
                    node_type="TRACK",
                    label=f"{cam_id} #{link.track_id}",
                    reference_id=str(link.track_id),
                    properties={
                        "camera_id": cam_id,
                        "track_id": link.track_id,
                        "match_score": link.match_score,
                        "match_status": link.match_status,
                        "first_seen": link.first_timestamp.isoformat(),
                        "last_seen": link.last_timestamp.isoformat(),
                        "evidence": link.evidence
                    }
                ))

                # Edge: Subject -> Observed_by -> Camera
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{subject.subject_id}-OBS-{cam_id}",
                    source=subject.subject_id,
                    target=cam_node_id,
                    relationship="OBSERVED_BY",
                    confidence=1.0,
                    properties={"camera_id": cam_id}
                ))

                # Edge: Track -> Observed_by -> Camera
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{track_node_id}-AT-{cam_id}",
                    source=track_node_id,
                    target=cam_node_id,
                    relationship="OCCURRED_AT",
                    confidence=1.0,
                    properties={}
                ))

                # Edge: Subject -> Track (MATCHED_TO)
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{subject.subject_id}-LINK-{track_node_id}",
                    source=subject.subject_id,
                    target=track_node_id,
                    relationship="MATCHED_TO",
                    confidence=link.match_score,
                    properties={
                        "match_score": link.match_score,
                        "match_status": link.match_status,
                        "evidence": link.evidence
                    }
                ))

                # Inter-camera hop edge: MOVED_TO
                if prev_cam_id and prev_cam_id != cam_id:
                    add_edge(GraphEdge(
                        edge_id=f"EDGE-MOVE-{prev_cam_id}-{cam_id}",
                        source=f"NODE-{prev_cam_id}",
                        target=cam_node_id,
                        relationship="MOVED_TO",
                        confidence=link.match_score,
                        properties={"transit_score": link.match_score}
                    ))

                prev_cam_id = cam_id
                prev_track_node_id = track_node_id

            # 3. Associated Events & Zones
            events = db.query(SecurityEventModel).filter(
                SecurityEventModel.track_id.in_([l.track_id for l in links]),
                SecurityEventModel.camera_id.in_([l.camera_id for l in links])
            ).order_by(SecurityEventModel.created_at.asc()).all()

            for evt in events:
                evt_node_id = f"NODE-{evt.event_id}"
                zone_node_id = f"NODE-{evt.zone_id}"

                # Event Node
                add_node(GraphNode(
                    node_id=evt_node_id,
                    node_type="EVENT",
                    label=f"{evt.event_type} ({evt.camera_id})",
                    reference_id=evt.event_id,
                    properties={
                        "event_id": evt.event_id,
                        "event_type": evt.event_type,
                        "camera_id": evt.camera_id,
                        "status": evt.status,
                        "created_at": evt.created_at.isoformat()
                    }
                ))

                # Zone Node
                add_node(GraphNode(
                    node_id=zone_node_id,
                    node_type="ZONE",
                    label=evt.zone_name,
                    reference_id=evt.zone_id,
                    properties={"zone_id": evt.zone_id, "camera_id": evt.camera_id}
                ))

                # Edge: Track -> Event
                track_node_id = f"NODE-{evt.camera_id}-TRK{evt.track_id}"
                rel_type = "ENTERED" if evt.event_type == "ZONE_ENTRY" else ("EXITED" if evt.event_type == "ZONE_EXIT" else "INTRUDED")
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{track_node_id}-EVT-{evt.event_id}",
                    source=track_node_id,
                    target=evt_node_id,
                    relationship=rel_type,
                    confidence=evt.confidence,
                    properties={"event_type": evt.event_type}
                ))

                # Edge: Event -> Zone (OCCURRED_AT)
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{evt_node_id}-ZONE-{evt.zone_id}",
                    source=evt_node_id,
                    target=zone_node_id,
                    relationship="OCCURRED_AT",
                    confidence=1.0,
                    properties={}
                ))

            # 4. Contextual Vehicle Associations
            vehicles = db.query(AssociatedVehicleModel).filter(
                AssociatedVehicleModel.subject_id == subject_id
            ).all()

            for veh in vehicles:
                veh_node_id = f"NODE-{veh.vehicle_subject_id}"
                add_node(GraphNode(
                    node_id=veh_node_id,
                    node_type="VEHICLE",
                    label=f"{veh.vehicle_subject_id} (VEHICLE)",
                    reference_id=veh.vehicle_subject_id,
                    properties={
                        "vehicle_id": veh.vehicle_subject_id,
                        "camera_id": veh.camera_id,
                        "proximity_meters": veh.proximity_meters,
                        "time_delta_seconds": veh.time_delta_seconds,
                        "notes": veh.notes
                    }
                ))

                # Edge: Subject -> Vehicle (ASSOCIATED_WITH)
                add_edge(GraphEdge(
                    edge_id=f"EDGE-{subject.subject_id}-VEH-{veh.vehicle_subject_id}",
                    source=subject.subject_id,
                    target=veh_node_id,
                    relationship="ASSOCIATED_WITH",
                    confidence=0.85,
                    properties={
                        "proximity_meters": veh.proximity_meters,
                        "time_delta_seconds": veh.time_delta_seconds,
                        "notes": veh.notes
                    }
                ))

            return IncidentGraph(
                incident_id=inc_id,
                subject_id=subject_id,
                nodes=list(nodes_dict.values()),
                edges=edges,
                generated_at=datetime.now(timezone.utc).isoformat()
            )

        finally:
            db.close()
