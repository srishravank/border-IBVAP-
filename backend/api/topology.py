from typing import List
from fastapi import APIRouter, HTTPException

from backend.models.subject import CameraTopologyResponse, CreateCameraTopologyRequest
from backend.services.topology_service import topology_service

router = APIRouter(tags=["Camera Topology"])


@router.get("/api/cameras/topology", response_model=List[CameraTopologyResponse])
@router.get("/api/topology", response_model=List[CameraTopologyResponse])
def get_all_topology_relations():
    """Returns all configured inter-camera spatial transitions and temporal constraints."""
    return topology_service.get_all_relations()


@router.get("/api/cameras/topology/{relation_id}", response_model=CameraTopologyResponse)
@router.get("/api/topology/{relation_id}", response_model=CameraTopologyResponse)
def get_topology_relation(relation_id: str):
    """Returns details for a specific camera topology relationship."""
    rel = topology_service.get_relation_by_id(relation_id)
    if not rel:
        raise HTTPException(status_code=404, detail=f"Camera topology relation '{relation_id}' not found")
    return rel


@router.post("/api/cameras/topology", response_model=CameraTopologyResponse)
@router.post("/api/topology", response_model=CameraTopologyResponse)
def create_or_update_topology_relation(req: CreateCameraTopologyRequest):
    """Creates or updates a camera topology relationship route."""
    return topology_service.create_relation(req)


@router.put("/api/cameras/topology/{relation_id}", response_model=CameraTopologyResponse)
@router.put("/api/topology/{relation_id}", response_model=CameraTopologyResponse)
def update_topology_relation(relation_id: str, req: CreateCameraTopologyRequest):
    """Updates an existing camera topology relationship."""
    updated = topology_service.update_relation(relation_id, req)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Camera topology relation '{relation_id}' not found")
    return updated


@router.delete("/api/cameras/topology/{relation_id}")
@router.delete("/api/topology/{relation_id}")
def delete_topology_relation(relation_id: str):
    """Deletes a camera topology relationship."""
    success = topology_service.delete_relation(relation_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Camera topology relation '{relation_id}' not found")
    return {"status": "success", "message": f"Topology relation '{relation_id}' deleted."}

