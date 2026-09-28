from fastapi import APIRouter, Query, HTTPException
from backend.services.simulation_engine import simulation_engine
from backend.services.demo_controller import demo_controller

router = APIRouter(prefix="/api/demo", tags=["Deterministic Hackathon Demo & Scenarios"])


@router.get("/status")
def get_demo_status():
    """Returns the current state machine stage, active demonstration IDs, and system readiness."""
    return demo_controller.get_status()


@router.post("/hero-scenario")
@router.post("/master")
@router.post("/scenario/10")
def run_phase11_hero_demo():
    """Executes the complete 34-step deterministic hero demonstration scenario across all 10 architectural layers."""
    return demo_controller.run_hero_scenario()


@router.post("/step/{step_name}")
def execute_demo_step(step_name: str):
    """Executes an individual stage of the demonstration state machine for interactive live jury presentations."""
    res = demo_controller.execute_step(step_name)
    if res.get("status") == "ERROR":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/cross-camera/journey")
@router.post("/scenario/4")
def run_cross_camera_journey_demo():
    """Triggers deterministic 3-camera subject journey simulation across CAM-01 -> CAM-02 -> CAM-03."""
    return simulation_engine.run_multi_camera_journey_demo()


@router.post("/cross-camera/false-match")
def run_false_match_rejection_demo():
    """Demonstrates rejection of incompatible tracks without forging a false global link."""
    return simulation_engine.run_false_match_rejection_demo()


@router.post("/scenario/1")
def run_scenario_1():
    """Scenario 1: Normal Movement (Daylight, outside restricted zones) -> LOW risk."""
    return simulation_engine.run_scenario_1_normal_movement()


@router.post("/scenario/2")
def run_scenario_2():
    """Scenario 2: Verified Zone Entry -> MEDIUM risk."""
    return simulation_engine.run_scenario_2_verified_zone_entry()


@router.post("/scenario/3")
def run_scenario_3():
    """Scenario 3: Night Intrusion (Restricted zone + fence crossing + night period) -> HIGH risk."""
    return simulation_engine.run_scenario_3_night_intrusion()


@router.post("/scenario/5")
def run_scenario_5():
    """Scenario 5: Person + Vehicle Association -> Related vehicle activity."""
    return simulation_engine.run_scenario_5_person_vehicle_association()


@router.post("/scenario/6")
def run_scenario_6():
    """Scenario 6: Multi-Factor Full Incident -> Full explainable factor breakdown."""
    return simulation_engine.run_scenario_6_multi_factor_incident()


@router.post("/scenario/9")
@router.post("/federated/demo")
def run_phase9_learning_demo():
    """Scenario 9: Phase 9 On-Device Fine-Tuning + FedAvg Aggregation + Model Governance."""
    return simulation_engine.run_phase9_learning_demo()


@router.post("/reset")
@router.post("/cross-camera/reset")
def reset_cross_camera_demo_state():
    """Resets cross-camera subjects, links, incidents, risk assessments, and vehicle associations to clean baseline."""
    return demo_controller.reset_demo()

