import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime, timezone

from backend.database.connection import SessionLocal
from backend.database.models import ZoneModel
from backend.models.zone import ZoneCreate, ZoneUpdate, ZoneResponse, ZoneType, ZoneSensitivity
from verification.polygon_engine import validate_polygon

logger = logging.getLogger("ibvap.zones")


class ZoneEngine:
    """
    Central Virtual Fence Zone Manager.
    Coordinates polygon persistence, in-memory caching, and validation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._zones_cache: Dict[str, List[ZoneResponse]] = {}  # camera_id -> List[ZoneResponse]
        self.is_loaded = False

    def load_zones_from_db(self):
        """Loads all configured zones from SQLite database into memory cache."""
        with self._lock:
            self._zones_cache.clear()
            db = SessionLocal()
            try:
                records = db.query(ZoneModel).all()
                for rec in records:
                    resp = self._model_to_response(rec)
                    if rec.camera_id not in self._zones_cache:
                        self._zones_cache[rec.camera_id] = []
                    self._zones_cache[rec.camera_id].append(resp)
                self.is_loaded = True
                logger.info(f"Loaded {len(records)} virtual fence zones across {len(self._zones_cache)} cameras.")
            finally:
                db.close()

    def _model_to_response(self, model: ZoneModel) -> ZoneResponse:
        return ZoneResponse(
            zone_id=model.zone_id,
            camera_id=model.camera_id,
            zone_name=model.zone_name,
            zone_type=ZoneType(model.zone_type),
            polygon=model.polygon,
            enabled=model.enabled,
            sensitivity=ZoneSensitivity(model.sensitivity),
            description=model.description or "",
            color=model.color or "#F43F5E",
            created_at=model.created_at.isoformat() if model.created_at else ""
        )

    def get_zones_for_camera(self, camera_id: str, enabled_only: bool = False) -> List[ZoneResponse]:
        if not self.is_loaded:
            self.load_zones_from_db()
        with self._lock:
            zones = self._zones_cache.get(camera_id, [])
            if enabled_only:
                return [z for z in zones if z.enabled]
            return list(zones)

    def get_all_zones(self) -> List[ZoneResponse]:
        if not self.is_loaded:
            self.load_zones_from_db()
        with self._lock:
            all_z = []
            for z_list in self._zones_cache.values():
                all_z.extend(z_list)
            return all_z

    def get_zone(self, zone_id: str) -> Optional[ZoneResponse]:
        db = SessionLocal()
        try:
            rec = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_id).first()
            return self._model_to_response(rec) if rec else None
        finally:
            db.close()

    def create_zone(self, data: ZoneCreate) -> ZoneResponse:
        """Validates polygon geometry and registers a new virtual fence zone."""
        # 1. Validate polygon
        valid, msg = validate_polygon(data.polygon)
        if not valid:
            raise ValueError(f"Invalid polygon geometry: {msg}")

        # 2. Assign ID if not provided
        zone_id = data.zone_id or f"ZONE-{data.camera_id}-{int(datetime.now(timezone.utc).timestamp() * 1000) % 10000:04d}"

        db = SessionLocal()
        try:
            existing = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_id).first()
            if existing:
                raise ValueError(f"Zone with ID '{zone_id}' already exists")

            model = ZoneModel(
                zone_id=zone_id,
                camera_id=data.camera_id,
                zone_name=data.zone_name,
                zone_type=data.zone_type.value,
                polygon_json=str(data.polygon),
                enabled=data.enabled,
                sensitivity=data.sensitivity.value,
                description=data.description,
                color=data.color or "#F43F5E"
            )
            db.add(model)
            db.commit()
            db.refresh(model)

            resp = self._model_to_response(model)
            # Update cache
            with self._lock:
                if data.camera_id not in self._zones_cache:
                    self._zones_cache[data.camera_id] = []
                self._zones_cache[data.camera_id].append(resp)

            logger.info(f"Created virtual zone '{zone_id}' on camera '{data.camera_id}' ({len(data.polygon)} vertices)")
            return resp
        finally:
            db.close()

    def update_zone(self, zone_id: str, update: ZoneUpdate) -> ZoneResponse:
        """Updates virtual zone parameters."""
        if update.polygon is not None:
            valid, msg = validate_polygon(update.polygon)
            if not valid:
                raise ValueError(f"Invalid polygon geometry: {msg}")

        db = SessionLocal()
        try:
            rec = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_id).first()
            if not rec:
                raise KeyError(f"Zone '{zone_id}' not found")

            if update.zone_name is not None:
                rec.zone_name = update.zone_name
            if update.zone_type is not None:
                rec.zone_type = update.zone_type.value
            if update.polygon is not None:
                rec.polygon = update.polygon
            if update.enabled is not None:
                rec.enabled = update.enabled
            if update.sensitivity is not None:
                rec.sensitivity = update.sensitivity.value
            if update.description is not None:
                rec.description = update.description
            if update.color is not None:
                rec.color = update.color

            db.commit()
            db.refresh(rec)

            resp = self._model_to_response(rec)
            self.load_zones_from_db()  # Refresh cache
            return resp
        finally:
            db.close()

    def delete_zone(self, zone_id: str) -> bool:
        """Deletes a virtual fence zone."""
        db = SessionLocal()
        try:
            rec = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_id).first()
            if not rec:
                return False
            db.delete(rec)
            db.commit()
            self.load_zones_from_db()
            logger.info(f"Deleted virtual zone '{zone_id}'")
            return True
        finally:
            db.close()


# Global singleton zone engine instance
zone_engine = ZoneEngine()
