import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.models.event import CameraEvent
from backend.services.camera_manager import camera_manager

logger = logging.getLogger("ibvap.websocket")

router = APIRouter(tags=["WebSocket"])

active_connections: Set[WebSocket] = set()
_loop: asyncio.AbstractEventLoop = None


def set_event_loop(loop: asyncio.AbstractEventLoop):
    global _loop
    _loop = loop


def on_camera_event_dispatch(event: CameraEvent):
    """Callback invoked by CameraManager when an event occurs; broadcasts to WebSocket clients."""
    if not active_connections or not _loop or _loop.is_closed():
        return

    payload = json.dumps(event.model_dump())
    
    async def _send_all():
        disconnected = []
        for ws in list(active_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            active_connections.discard(ws)

    asyncio.run_coroutine_threadsafe(_send_all(), _loop)


def broadcast_command_event(event_dict: dict):
    """Broadcasts arbitrary command and lifecycle events to active WebSocket clients."""
    if not active_connections or not _loop or _loop.is_closed():
        return

    payload = json.dumps(event_dict)

    async def _send_all():
        disconnected = []
        for ws in list(active_connections):
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            active_connections.discard(ws)

    asyncio.run_coroutine_threadsafe(_send_all(), _loop)


# Connect event handler to camera manager
camera_manager.register_event_subscriber(on_camera_event_dispatch)


@router.websocket("/api/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time camera health events and status updates."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Active clients: {len(active_connections)}")

    # Send initial snapshot of all camera statuses
    try:
        cams = camera_manager.get_all_cameras()
        initial_msg = {
            "event_type": "INITIAL_STATE",
            "cameras": [c.model_dump() for c in cams]
        }
        await websocket.send_text(json.dumps(initial_msg))

        while True:
            # Keepalive / handle client ping-pongs
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Active clients: {len(active_connections)}")
