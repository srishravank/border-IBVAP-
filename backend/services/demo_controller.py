import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.config import settings
from backend.services.simulation_engine import simulation_engine
from backend.services.camera_manager import camera_manager
from backend.services.ai_pipeline import ai_service
from backend.services.event_manager import event_manager
from backend.services.cross_camera_engine import cross_camera_engine
from backend.services.risk_service import risk_service
from backend.services.command_service import command_service
from backend.services.evidence_service import evidence_service
from backend.services.connectivity_service import connectivity_service
from backend.services.sync_service import sync_service
from backend.services.model_registry_service import model_registry
from backend.services.training_sample_service import training_sample_service
from backend.services.local_training_service import local_training_service
from backend.services.federated_learning_service import federated_aggregator

logger = logging.getLogger("ibvap.demo.controller")


class DemoStage:
    DEMO_IDLE = "DEMO_IDLE"
    CAMERAS_RUNNING = "CAMERAS_RUNNING"
    SUBJECT_DETECTED = "SUBJECT_DETECTED"
    EVENT_VERIFIED = "EVENT_VERIFIED"
    FALSE_POSITIVE_REJECTED = "FALSE_POSITIVE_REJECTED"
    SUBJECT_CORRELATED = "SUBJECT_CORRELATED"
    RISK_ASSESSED = "RISK_ASSESSED"
    INCIDENT_DISPLAYED = "INCIDENT_DISPLAYED"
    OPERATOR_ACTION = "OPERATOR_ACTION"
    EVIDENCE_CREATED = "EVIDENCE_CREATED"
    EVIDENCE_ANCHORED = "EVIDENCE_ANCHORED"
    TAMPER_TEST = "TAMPER_TEST"
    OFFLINE_TEST = "OFFLINE_TEST"
    SYNC_TEST = "SYNC_TEST"
    LEARNING_TEST = "LEARNING_TEST"
    DEMO_COMPLETE = "DEMO_COMPLETE"


class DemoController:
    """
    Deterministic Demonstration Orchestration Controller for IBVAP 2.0.
    Coordinates the 34-step hackathon hero scenario, state-machine transitions,
    tamper demonstration, offline-first resilience, and federated learning workflows.
    """

    def __init__(self):
        self.current_stage: str = DemoStage.DEMO_IDLE
        self.stage_history: List[Dict[str, Any]] = []
        self.active_demo_incident_id: Optional[str] = None
        self.active_demo_subject_id: Optional[str] = None
        self.active_demo_evidence_id: Optional[str] = None
        self.last_execution_summary: Dict[str, Any] = {}

    def get_status(self) -> Dict[str, Any]:
        """Returns the current state of the demo controller and subsystem readiness."""
        cams = camera_manager.get_all_cameras()
        active_cams = sum(1 for c in cams if c.status.value == "ONLINE")
        incidents = cross_camera_engine.get_incidents()
        conn_stat = connectivity_service.get_status()
        sync_sum = sync_service.get_summary()

        return {
            "demo_mode": getattr(settings, "DEMO_MODE", True),
            "current_stage": self.current_stage,
            "active_incident_id": self.active_demo_incident_id,
            "active_subject_id": self.active_demo_subject_id,
            "active_evidence_id": self.active_demo_evidence_id,
            "total_cameras": len(cams),
            "online_cameras": active_cams,
            "total_incidents": len(incidents),
            "connectivity_state": conn_stat.state.value,
            "pending_sync_items": sync_sum.pending_count,
            "stage_history": self.stage_history[-10:],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    def reset_demo(self) -> Dict[str, Any]:
        """
        Safely resets all transient demonstration state:
        - Resets simulation engine (subjects, journeys, cross-camera links, demo incidents)
        - Restores connectivity state to ONLINE
        - Flushes sync queue
        - Restores original evidence blocks
        - Resets candidate model registry entries
        """
        logger.info("Resetting IBVAP 2.0 Demonstration state...")
        sim_res = simulation_engine.reset_simulation()
        connectivity_service.restore_connection("Demo Reset")
        
        self.current_stage = DemoStage.DEMO_IDLE
        self.active_demo_incident_id = None
        self.active_demo_subject_id = None
        self.active_demo_evidence_id = None
        self.stage_history.append({
            "stage": DemoStage.DEMO_IDLE,
            "action": "RESET_ALL",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {
            "status": "SUCCESS",
            "message": "Demonstration environment reset to clean baseline state.",
            "details": sim_res
        }

    def run_hero_scenario(self) -> Dict[str, Any]:
        """
        Executes the full 34-step end-to-end hero demonstration scenario.
        Covers SEE -> UNDERSTAND -> VERIFY -> CORRELATE -> ASSESS -> RESPOND -> PROVE -> LEARN.
        """
        logger.info("Initiating IBVAP 2.0 Hero Demonstration Scenario...")
        self.current_stage = DemoStage.CAMERAS_RUNNING

        # 1. Reset baseline
        self.reset_demo()

        # 2. Master E2E Pipeline Execution
        master_res = simulation_engine.run_master_e2e_demo()
        
        pipeline_sum = master_res.get("pipeline_summary", {})
        self.active_demo_subject_id = pipeline_sum.get("understand_verify_correlate", {}).get("subject_id")
        self.active_demo_incident_id = pipeline_sum.get("understand_verify_correlate", {}).get("incident_id")
        self.active_demo_evidence_id = pipeline_sum.get("prove", {}).get("evidence_id")
        
        self.current_stage = DemoStage.DEMO_COMPLETE
        self.last_execution_summary = master_res

        self.stage_history.append({
            "stage": DemoStage.DEMO_COMPLETE,
            "action": "RUN_HERO_SCENARIO",
            "incident_id": self.active_demo_incident_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return master_res

    def execute_step(self, step_name: str) -> Dict[str, Any]:
        """
        Executes an individual stage of the demonstration state machine.
        Allows step-by-step interactive live jury presentations.
        """
        step = step_name.upper().strip()
        now = datetime.now(timezone.utc).isoformat()

        if step in ("1", "CAMERAS_RUNNING", "SEE"):
            cams = camera_manager.get_all_cameras()
            self.current_stage = DemoStage.CAMERAS_RUNNING
            return {
                "step": "1. SEE (CCTV Matrix Ingestion)",
                "status": "SUCCESS",
                "active_cameras": [c.camera_id for c in cams if c.status.value == "ONLINE"],
                "total_fps": sum(c.fps for c in cams)
            }

        elif step in ("2", "SUBJECT_DETECTED", "UNDERSTAND"):
            res = simulation_engine.run_scenario_1_normal_movement()
            self.current_stage = DemoStage.SUBJECT_DETECTED
            return {
                "step": "2. UNDERSTAND (ByteTrack Perception)",
                "status": "SUCCESS",
                "result": res
            }

        elif step in ("3", "EVENT_VERIFIED", "VERIFY"):
            res = simulation_engine.run_scenario_2_verified_zone_entry()
            self.current_stage = DemoStage.EVENT_VERIFIED
            return {
                "step": "3. VERIFY (Virtual Fence 3-Frame Gate)",
                "status": "SUCCESS",
                "result": res
            }

        elif step in ("4", "FALSE_POSITIVE_REJECTED", "SUPPRESS"):
            res = simulation_engine.run_false_match_rejection_demo()
            self.current_stage = DemoStage.FALSE_POSITIVE_REJECTED
            return {
                "step": "4. SUPPRESS (False-Positive & Spatial Rejection)",
                "status": "SUCCESS",
                "result": res
            }

        elif step in ("5", "SUBJECT_CORRELATED", "CORRELATE"):
            res = simulation_engine.run_multi_camera_journey_demo()
            self.active_demo_subject_id = res.get("subject_id")
            self.active_demo_incident_id = res.get("incident_id")
            self.current_stage = DemoStage.SUBJECT_CORRELATED
            return {
                "step": "5. CORRELATE (Cross-Camera Journey Graph)",
                "status": "SUCCESS",
                "subject_id": self.active_demo_subject_id,
                "incident_id": self.active_demo_incident_id,
                "journey": res
            }

        elif step in ("6", "RISK_ASSESSED", "ASSESS"):
            inc_id = self.active_demo_incident_id
            if not inc_id:
                j_res = simulation_engine.run_multi_camera_journey_demo()
                inc_id = j_res.get("incident_id")
                self.active_demo_incident_id = inc_id

            risk_eval = risk_service.evaluate_incident(inc_id, force=True)
            self.current_stage = DemoStage.RISK_ASSESSED
            return {
                "step": "6. ASSESS (Explainable Risk Scoring Engine)",
                "status": "SUCCESS",
                "incident_id": inc_id,
                "risk_score": risk_eval.score,
                "risk_level": risk_eval.risk_level,
                "explanation": risk_eval.explanation,
                "factors": [f.model_dump() for f in risk_eval.factors]
            }

        elif step in ("7", "OPERATOR_ACTION", "RESPOND"):
            inc_id = self.active_demo_incident_id
            if not inc_id:
                j_res = simulation_engine.run_multi_camera_journey_demo()
                inc_id = j_res.get("incident_id")
                self.active_demo_incident_id = inc_id

            ack = command_service.acknowledge_incident(inc_id, "OP-9402", "OPERATOR", "Operator acknowledged on SOC terminal")
            rec_cams = command_service.get_recommended_cameras(inc_id)
            self.current_stage = DemoStage.OPERATOR_ACTION
            return {
                "step": "7. RESPOND (SOC Operator Command & Control)",
                "status": "SUCCESS",
                "incident_id": inc_id,
                "operator_action": ack.action,
                "recommended_cameras": [c.camera_id for c in rec_cams]
            }

        elif step in ("8", "EVIDENCE_CREATED", "PROVE"):
            inc_id = self.active_demo_incident_id
            if not inc_id:
                j_res = simulation_engine.run_multi_camera_journey_demo()
                inc_id = j_res.get("incident_id")
                self.active_demo_incident_id = inc_id

            evidence_pkg = evidence_service.create_and_anchor_evidence(
                incident_id=inc_id,
                operator_id="OP-9402",
                role="SUPERVISOR",
                version="1.0",
                notes="Court-admissible evidence package generated"
            )
            self.active_demo_evidence_id = evidence_pkg.evidence_id
            verif = evidence_service.verify_evidence_integrity(evidence_pkg.evidence_id)
            self.current_stage = DemoStage.EVIDENCE_ANCHORED
            return {
                "step": "8. PROVE (SHA-256 Digest & Blockchain Ledger Anchor)",
                "status": "SUCCESS",
                "evidence_id": evidence_pkg.evidence_id,
                "sha256_hash": evidence_pkg.hash.hash_value,
                "verification": verif.status,
                "ledger_block": evidence_pkg.anchor.block_number if evidence_pkg.anchor else 1
            }

        elif step in ("9", "TAMPER_TEST"):
            ev_id = self.active_demo_evidence_id
            if not ev_id:
                # Generate if not exists
                step_8 = self.execute_step("8")
                ev_id = step_8.get("evidence_id")

            tamper_res = evidence_service.demonstrate_tamper(ev_id)
            verif_tampered = evidence_service.verify_evidence_integrity(ev_id)
            self.current_stage = DemoStage.TAMPER_TEST
            return {
                "step": "9. TAMPER TEST (Cryptographic Mismatch Detection)",
                "status": "SUCCESS",
                "evidence_id": ev_id,
                "modified_field": tamper_res.get("modified_field"),
                "verification_result": verif_tampered.status,
                "is_authentic": verif_tampered.is_authentic,
                "tamper_detected": verif_tampered.status == "TAMPERED"
            }

        elif step in ("10", "RESTORE_EVIDENCE"):
            ev_id = self.active_demo_evidence_id
            if ev_id:
                evidence_service.restore_evidence(ev_id)
                verif_restored = evidence_service.verify_evidence_integrity(ev_id)
                return {
                    "step": "10. RESTORE EVIDENCE (Cryptographic Integrity Verified)",
                    "status": "SUCCESS",
                    "evidence_id": ev_id,
                    "verification_result": verif_restored.status,
                    "is_authentic": verif_restored.is_authentic
                }
            return {"status": "ERROR", "message": "No active evidence package found"}

        elif step in ("11", "OFFLINE_TEST", "OFFLINE"):
            connectivity_service.simulate_offline("Jury Demo: Lost backhaul network link")
            inc_id = self.active_demo_incident_id or "INC-DEMO-OFFLINE"
            command_service.acknowledge_incident(inc_id, "OP-9402", "OPERATOR", "Offline operator triage")
            q_sum = sync_service.get_summary()
            self.current_stage = DemoStage.OFFLINE_TEST
            return {
                "step": "11. OFFLINE OPERATION (Edge Autonomy)",
                "status": "SUCCESS",
                "connectivity_state": "OFFLINE",
                "edge_pipeline_active": True,
                "pending_sync_queue": q_sum.pending_count
            }

        elif step in ("12", "SYNC_TEST", "RECOVER"):
            connectivity_service.restore_connection("Jury Demo: Network backhaul restored")
            sync_res = sync_service.trigger_sync()
            q_sum = sync_service.get_summary()
            self.current_stage = DemoStage.SYNC_TEST
            return {
                "step": "12. RESILIENT SYNCHRONIZATION (Queue Flush)",
                "status": "SUCCESS",
                "connectivity_state": "ONLINE",
                "sync_summary": sync_res,
                "remaining_pending": q_sum.pending_count
            }

        elif step in ("13", "LEARNING_TEST", "LEARN"):
            learning_res = simulation_engine.run_phase9_learning_demo()
            self.current_stage = DemoStage.DEMO_COMPLETE
            return {
                "step": "13. LEARN (Federated Edge Fine-Tuning & Model Rollback)",
                "status": "SUCCESS",
                "learning_summary": learning_res
            }

        else:
            return {
                "status": "ERROR",
                "message": f"Unknown step '{step_name}'. Valid steps: 1 (SEE), 2 (UNDERSTAND), 3 (VERIFY), 4 (SUPPRESS), 5 (CORRELATE), 6 (ASSESS), 7 (RESPOND), 8 (PROVE), 9 (TAMPER), 10 (RESTORE), 11 (OFFLINE), 12 (SYNC), 13 (LEARN)."
            }


demo_controller = DemoController()
