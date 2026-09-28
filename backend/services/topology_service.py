import logging
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from backend.database.connection import SessionLocal
from backend.database.models import CameraTopologyModel
from backend.models.subject import CameraTopologyResponse, CreateCameraTopologyRequest
from intelligence.topology.camera_topology import CameraTopologyGraph, CameraRelation

logger = logging.getLogger("ibvap.topology")


class TopologyService:
    """
    Manages camera topology route storage in SQLite and synchronization
    with the in-memory CameraTopologyGraph.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.graph = CameraTopologyGraph()
        self.is_loaded = False

    def load_topology_from_db(self):
        """Loads all camera topology relationships from SQLite into the in-memory graph."""
        with self._lock:
            self.graph.clear()
            db = SessionLocal()
            try:
                models = db.query(CameraTopologyModel).all()
                for m in models:
                    rel = CameraRelation(
                        relation_id=m.relation_id,
                        source_camera=m.source_camera,
                        destination_camera=m.destination_camera,
                        min_transition_seconds=m.min_transition_seconds,
                        max_transition_seconds=m.max_transition_seconds,
                        distance_meters=m.distance_meters,
                        direction=m.direction,
                        enabled=m.enabled,
                        description=m.description or ""
                    )
                    self.graph.add_relation(rel)
                self.is_loaded = True
                logger.info(f"Loaded {len(models)} camera topology relations into memory graph.")
            finally:
                db.close()

    def get_all_relations(self) -> List[CameraTopologyResponse]:
        db = SessionLocal()
        try:
            models = db.query(CameraTopologyModel).order_by(CameraTopologyModel.created_at.asc()).all()
            return [
                CameraTopologyResponse(
                    relation_id=m.relation_id,
                    source_camera=m.source_camera,
                    destination_camera=m.destination_camera,
                    min_transition_seconds=m.min_transition_seconds,
                    max_transition_seconds=m.max_transition_seconds,
                    distance_meters=m.distance_meters,
                    direction=m.direction,
                    enabled=m.enabled,
                    description=m.description,
                    created_at=m.created_at.isoformat()
                )
                for m in models
            ]
        finally:
            db.close()

    def get_relation_by_id(self, relation_id: str) -> Optional[CameraTopologyResponse]:
        db = SessionLocal()
        try:
            m = db.query(CameraTopologyModel).filter(CameraTopologyModel.relation_id == relation_id).first()
            if not m:
                return None
            return CameraTopologyResponse(
                relation_id=m.relation_id,
                source_camera=m.source_camera,
                destination_camera=m.destination_camera,
                min_transition_seconds=m.min_transition_seconds,
                max_transition_seconds=m.max_transition_seconds,
                distance_meters=m.distance_meters,
                direction=m.direction,
                enabled=m.enabled,
                description=m.description,
                created_at=m.created_at.isoformat()
            )
        finally:
            db.close()

    def create_relation(self, req: CreateCameraTopologyRequest) -> CameraTopologyResponse:
        db = SessionLocal()
        try:
            rel_id = f"TOPO-{req.source_camera}-{req.destination_camera}"
            # Check if exists
            existing = db.query(CameraTopologyModel).filter(CameraTopologyModel.relation_id == rel_id).first()
            if existing:
                existing.min_transition_seconds = req.min_transition_seconds
                existing.max_transition_seconds = req.max_transition_seconds
                existing.distance_meters = req.distance_meters
                existing.direction = req.direction
                existing.enabled = req.enabled
                existing.description = req.description
                db.commit()
                db.refresh(existing)
                m = existing
            else:
                m = CameraTopologyModel(
                    relation_id=rel_id,
                    source_camera=req.source_camera,
                    destination_camera=req.destination_camera,
                    min_transition_seconds=req.min_transition_seconds,
                    max_transition_seconds=req.max_transition_seconds,
                    distance_meters=req.distance_meters,
                    direction=req.direction,
                    enabled=req.enabled,
                    description=req.description
                )
                db.add(m)
                db.commit()
                db.refresh(m)

            self.load_topology_from_db()
            return CameraTopologyResponse(
                relation_id=m.relation_id,
                source_camera=m.source_camera,
                destination_camera=m.destination_camera,
                min_transition_seconds=m.min_transition_seconds,
                max_transition_seconds=m.max_transition_seconds,
                distance_meters=m.distance_meters,
                direction=m.direction,
                enabled=m.enabled,
                description=m.description,
                created_at=m.created_at.isoformat()
            )
        finally:
            db.close()

    def update_relation(self, relation_id: str, req: CreateCameraTopologyRequest) -> Optional[CameraTopologyResponse]:
        db = SessionLocal()
        try:
            m = db.query(CameraTopologyModel).filter(CameraTopologyModel.relation_id == relation_id).first()
            if not m:
                return None
            m.source_camera = req.source_camera
            m.destination_camera = req.destination_camera
            m.min_transition_seconds = req.min_transition_seconds
            m.max_transition_seconds = req.max_transition_seconds
            m.distance_meters = req.distance_meters
            m.direction = req.direction
            m.enabled = req.enabled
            m.description = req.description
            db.commit()
            db.refresh(m)
            self.load_topology_from_db()
            return CameraTopologyResponse(
                relation_id=m.relation_id,
                source_camera=m.source_camera,
                destination_camera=m.destination_camera,
                min_transition_seconds=m.min_transition_seconds,
                max_transition_seconds=m.max_transition_seconds,
                distance_meters=m.distance_meters,
                direction=m.direction,
                enabled=m.enabled,
                description=m.description,
                created_at=m.created_at.isoformat()
            )
        finally:
            db.close()

    def delete_relation(self, relation_id: str) -> bool:
        db = SessionLocal()
        try:
            m = db.query(CameraTopologyModel).filter(CameraTopologyModel.relation_id == relation_id).first()
            if not m:
                return False
            db.delete(m)
            db.commit()
            self.load_topology_from_db()
            return True
        finally:
            db.close()


# Singleton instance
topology_service = TopologyService()
