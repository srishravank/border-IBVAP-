from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """
    Node in the border surveillance Incident Graph.
    Types: SUBJECT, CAMERA, TRACK, ZONE, EVENT, VEHICLE
    """
    node_id: str = Field(..., description="Unique graph node ID (e.g. SUBJ-001, CAM-01, EVT-001)")
    node_type: str = Field(..., description="'SUBJECT', 'CAMERA', 'TRACK', 'ZONE', 'EVENT', 'VEHICLE'")
    label: str = Field(..., description="Human-readable node label")
    reference_id: str = Field(..., description="Underlying database record or identifier")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadata properties (timestamps, coordinates, confidence)")


class GraphEdge(BaseModel):
    """
    Directed relationship edge between two nodes in the Incident Graph.
    Relationships: OBSERVED_BY, MATCHED_TO, ENTERED, EXITED, MOVED_TO, ASSOCIATED_WITH, OCCURRED_AT
    """
    edge_id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node_id")
    target: str = Field(..., description="Target node_id")
    relationship: str = Field(..., description="Typed relationship name")
    confidence: float = Field(default=1.0, description="Confidence/weight of relationship in [0.0, 1.0]")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata (transit times, distance, factors)")


class IncidentGraph(BaseModel):
    """Complete serialized Incident Graph."""
    incident_id: str = Field(..., description="Parent incident identifier")
    subject_id: str = Field(..., description="Primary subject identifier")
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    generated_at: str = Field(..., description="ISO 8601 UTC timestamp of graph generation")
