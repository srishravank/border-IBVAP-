import asyncio
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from backend.models.camera import (
    CameraConfigCreate,
    CameraConfigUpdate,
    CameraResponse,
    CameraStatusResponse
)
from backend.models.event import CameraEvent
from backend.services.camera_manager import camera_manager
from backend.database.connection import get_db
from backend.database.models import CameraModel, CameraHealthEventModel

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])


@router.get("", response_model=List[CameraResponse])
def get_cameras():
    """Returns all registered CCTV cameras with current runtime health and metrics."""
    return camera_manager.get_all_cameras()


@router.post("", response_model=CameraResponse, status_code=201)
def create_camera(config: CameraConfigCreate):
    """Registers a new CCTV camera and automatically initializes its ingestion stream."""
    try:
        return camera_manager.register_camera(config)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: str):
    """Returns configuration and status for a specific camera."""
    try:
        return camera_manager.get_camera_response(camera_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")


@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: str, update: CameraConfigUpdate):
    """Updates camera parameters and dynamically adjusts running ingestion worker."""
    try:
        return camera_manager.update_camera(camera_id, update)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{camera_id}")
def delete_camera(camera_id: str):
    """Stops ingestion and removes camera from configuration."""
    success = camera_manager.delete_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    return {"status": "success", "message": f"Camera '{camera_id}' deleted"}


@router.get("/{camera_id}/status", response_model=CameraStatusResponse)
def get_camera_status(camera_id: str):
    """Returns current health, FPS, resolution, frame counter, and uptime."""
    try:
        return camera_manager.get_camera_status(camera_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")


@router.post("/{camera_id}/start")
def start_camera(camera_id: str):
    """Starts ingestion for a specific camera."""
    success = camera_manager.start_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found or could not be started")
    return {"status": "success", "message": f"Camera '{camera_id}' ingestion started"}


@router.post("/{camera_id}/stop")
def stop_camera(camera_id: str):
    """Stops ingestion for a specific camera."""
    success = camera_manager.stop_camera(camera_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    return {"status": "success", "message": f"Camera '{camera_id}' ingestion stopped"}


@router.get("/{camera_id}/events")
def get_camera_events(
    camera_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves recent health events and alarms logged for this camera."""
    events = (
        db.query(CameraHealthEventModel)
        .filter(CameraHealthEventModel.camera_id == camera_id)
        .order_by(CameraHealthEventModel.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": evt.id,
            "camera_id": evt.camera_id,
            "event_type": evt.event_type,
            "timestamp": evt.timestamp.isoformat() if evt.timestamp else "",
            "frame_id": evt.frame_id,
            "description": evt.description,
            "details": evt.details
        }
        for evt in events
    ]


@router.get("/{camera_id}/snapshot")
def get_camera_snapshot(camera_id: str, annotated: bool = Query(default=True)):
    """Returns the latest captured frame as a single JPEG image with automatic fallback."""
    from backend.services.ai_pipeline import ai_service
    import cv2
    import numpy as np

    jpeg_bytes = None
    if annotated:
        jpeg_bytes = ai_service.get_annotated_jpeg(camera_id)
    if not jpeg_bytes:
        jpeg_bytes = camera_manager.get_latest_frame_jpeg(camera_id)

    if not jpeg_bytes:
        # Generate clean tactical placeholder
        ph = np.zeros((720, 1280, 3), dtype=np.uint8)
        ph[:, :] = (15, 20, 25)
        cv2.putText(ph, f"[{camera_id}] BORDER SENSOR FEED INITIALIZING...", (320, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 220, 255), 2)
        _, enc = cv2.imencode(".jpg", ph, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        jpeg_bytes = enc.tobytes()

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@router.get("/{camera_id}/preview")
async def preview_stream(camera_id: str, annotated: bool = Query(default=True)):
    """
    MJPEG live preview stream for browser and dashboard viewing.
    Streams AI-annotated frames (bounding boxes, persistent IDs, trails) by default.
    Falls back smoothly to raw capture frame when annotation is pending or initializing.
    """
    from backend.services.ai_pipeline import ai_service

    worker = camera_manager.workers.get(camera_id)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    async def frame_generator():
        try:
            while True:
                jpeg_bytes = None
                if annotated:
                    jpeg_bytes = ai_service.get_annotated_jpeg(camera_id)

                if not jpeg_bytes:
                    frame_pkt = worker.get_latest_frame()
                    if frame_pkt:
                        jpeg_bytes = frame_pkt.to_jpeg(quality=70)

                if jpeg_bytes:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
                    )
                # Smooth throttle (~25 FPS max)
                await asyncio.sleep(0.04)
        except (asyncio.CancelledError, GeneratorExit):
            pass
        except Exception:
            pass

    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )

