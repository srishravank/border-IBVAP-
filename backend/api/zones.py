from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.models.zone import ZoneCreate, ZoneUpdate, ZoneResponse
from backend.services.zone_engine import zone_engine

router = APIRouter(tags=["Virtual Zones"])


@router.get("/api/zones", response_model=List[ZoneResponse])
def get_all_zones():
    """Returns all configured virtual fence zones across all border cameras."""
    return zone_engine.get_all_zones()


@router.get("/api/cameras/{camera_id}/zones", response_model=List[ZoneResponse])
def get_camera_zones(camera_id: str, enabled_only: bool = Query(default=False)):
    """Returns all virtual fence zones configured for a specific camera."""
    return zone_engine.get_zones_for_camera(camera_id, enabled_only=enabled_only)


@router.post("/api/cameras/{camera_id}/zones", response_model=ZoneResponse, status_code=201)
def create_camera_zone(camera_id: str, zone_data: ZoneCreate):
    """Creates a new polygon-based virtual fence zone for the camera."""
    zone_data.camera_id = camera_id
    try:
        return zone_engine.create_zone(zone_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create zone: {e}")


@router.get("/api/zones/{zone_id}", response_model=ZoneResponse)
def get_zone(zone_id: str):
    """Returns configuration for a specific virtual fence zone."""
    zone = zone_engine.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    return zone


@router.put("/api/zones/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: str, update: ZoneUpdate):
    """Updates geometry or parameters for a virtual fence zone."""
    try:
        return zone_engine.update_zone(zone_id, update)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/zones/{zone_id}")
def delete_zone(zone_id: str):
    """Deletes a virtual fence zone."""
    success = zone_engine.delete_zone(zone_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    return {"status": "success", "message": f"Virtual zone '{zone_id}' deleted successfully"}
