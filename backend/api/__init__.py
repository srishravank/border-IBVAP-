from .cameras import router as cameras_router
from .websocket import router as ws_router
from .ai import router as ai_router
from .zones import router as zones_router
from .events import router as events_router

__all__ = ["cameras_router", "ws_router", "ai_router", "zones_router", "events_router"]
