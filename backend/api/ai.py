import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, Response

from backend.models.detection import DetectionResult, DetectionSummary
from backend.models.track import TrackedObject
from ai.schemas.observation import AIObservation
from backend.services.ai_pipeline import ai_service

router = APIRouter(prefix="/api", tags=["AI & Tracking"])


@router.get("/ai/status")
def get_ai_status():
    """Returns global Edge AI perception engine status, model info, and tracking telemetry."""
    return ai_service.get_global_status()


@router.get("/cameras/{camera_id}/detections", response_model=List[DetectionResult])
def get_camera_detections(camera_id: str):
    """Returns the most recent object detections (persons, vehicles) for a specific camera."""
    return ai_service.get_camera_detections(camera_id)


@router.get("/cameras/{camera_id}/tracks", response_model=List[TrackedObject])
def get_camera_tracks(camera_id: str):
    """Returns all active tracked objects with persistent IDs and trajectory history for this camera."""
    return ai_service.get_camera_tracks(camera_id)


@router.get("/cameras/{camera_id}/tracks/{track_id}", response_model=TrackedObject)
def get_camera_track_detail(camera_id: str, track_id: int):
    """Returns details and observed trajectory for a specific Track ID."""
    tracks = ai_service.get_camera_tracks(camera_id)
    for t in tracks:
        if t.track_id == track_id:
            return t
    raise HTTPException(status_code=404, detail=f"Track ID '{track_id}' not found for camera '{camera_id}'")


@router.get("/cameras/{camera_id}/performance")
def get_camera_performance(camera_id: str):
    """Returns real-time inference latency, detector time, tracker time, and FPS stats."""
    return ai_service.get_camera_performance(camera_id)


@router.get("/cameras/{camera_id}/observations", response_model=List[AIObservation])
def get_camera_observations(camera_id: str, limit: int = Query(default=20, ge=1, le=100)):
    """Returns standardized Edge AI Observations formatted for Phase 3 ingestion."""
    obs = ai_service.get_camera_observations(camera_id)
    return obs[:limit]


@router.get("/cameras/{camera_id}/ai_preview")
async def get_ai_annotated_preview_stream(camera_id: str):
    """
    Live MJPEG preview stream with AI visual overlays (bounding boxes, persistent IDs, trajectory trails).
    """
    pipe = ai_service.get_camera_pipeline(camera_id)
    if not pipe:
        raise HTTPException(status_code=404, detail=f"Camera AI pipeline '{camera_id}' not active")

    async def frame_generator():
        while True:
            jpeg_bytes = ai_service.get_annotated_jpeg(camera_id)
            if jpeg_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
                )
            await asyncio.sleep(0.04)

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
