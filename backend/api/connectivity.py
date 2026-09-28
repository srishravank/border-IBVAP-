import logging
from fastapi import APIRouter, HTTPException, status
from backend.models.sync import (
    ConnectivityStatusResponse,
    ConnectivitySimulationRequest,
)
from backend.services.connectivity_service import connectivity_service

logger = logging.getLogger(__name__)

connectivity_router = APIRouter(prefix="/api/system/connectivity", tags=["System Connectivity"])


@connectivity_router.get(
    "",
    response_model=ConnectivityStatusResponse,
    summary="Get Edge Connectivity Status",
    description="Returns current network connection state, heartbeat metrics, and simulation status."
)
def get_connectivity_status():
    return connectivity_service.get_status()


@connectivity_router.post(
    "/simulate",
    response_model=ConnectivityStatusResponse,
    summary="Simulate Network Loss / Recovery",
    description="Overrides connection state (e.g. OFFLINE, ONLINE) for testing and hackathon demonstrations."
)
def simulate_connectivity(req: ConnectivitySimulationRequest):
    logger.info(f"[API] Connectivity simulation requested: {req.state} (Reason: {req.reason})")
    if req.state.value == "OFFLINE":
        return connectivity_service.simulate_offline(reason=req.reason or "Simulated network disconnect")
    elif req.state.value in ("ONLINE", "RECONNECTING"):
        return connectivity_service.restore_connection(reason=req.reason or "Simulated network recovery")
    else:
        connectivity_service.set_state(req.state, reason=req.reason or "Simulation override", is_simulated=True)
        return connectivity_service.get_status()
