import pytest
from datetime import datetime, timezone

from backend.database.connection import init_db, SessionLocal
from backend.database.models import IncidentModel, SubjectModel, RiskConfigurationModel
from backend.services.risk_service import risk_service
from backend.models.risk import UpdateRiskConfigurationPayload


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_risk_service_incident_lifecycle_and_history():
    db = SessionLocal()
    try:
        from backend.database.models import RiskFactorModel, RiskHistoryModel, RiskAssessmentModel
        db.query(RiskFactorModel).delete()
        db.query(RiskHistoryModel).delete()
        db.query(RiskAssessmentModel).delete()
        db.query(IncidentModel).filter(IncidentModel.incident_id == "INC-SERV-01").delete()
        db.query(SubjectModel).filter(SubjectModel.subject_id == "SUBJ-SERV-01").delete()
        db.commit()

        now_dt = datetime.now(timezone.utc)
        subj = SubjectModel(
            subject_id="SUBJ-SERV-01",
            object_type="person",
            status="ACTIVE",
            first_seen=now_dt,
            last_seen=now_dt,
            initial_camera_id="CAM-01",
            initial_track_id=10,
            total_cameras_visited=1,
            created_at=now_dt
        )
        db.add(subj)

        inc = IncidentModel(
            incident_id="INC-SERV-01",
            subject_id="SUBJ-SERV-01",
            status="ACTIVE",
            title="Service Test Incident",
            summary="Unit test",
            created_at=now_dt,
            updated_at=now_dt
        )
        db.add(inc)
        db.commit()
    finally:
        db.close()

    # 1. Evaluate incident risk
    res = risk_service.evaluate_incident("INC-SERV-01", force=True)
    assert res is not None
    assert res.incident_id == "INC-SERV-01"
    assert res.risk_level in ("LOW", "MEDIUM", "HIGH")
    assert len(res.factors) >= 6

    # 2. Query history
    history = risk_service.get_incident_risk_history("INC-SERV-01")
    assert len(history) >= 1
    assert history[0].incident_id == "INC-SERV-01"

    # 3. Query standardized Phase 6 intelligence
    intel = risk_service.get_incident_intelligence("INC-SERV-01")
    assert intel is not None
    assert intel.incident_id == "INC-SERV-01"
    assert "score" in intel.risk
    assert "level" in intel.risk


def test_risk_configuration_versioning():
    curr_cfg = risk_service.get_active_config()
    assert curr_cfg.is_active is True

    # Update config with custom weights
    payload = UpdateRiskConfigurationPayload(
        weights={"zone": 30.0, "fence": 30.0, "night": 20.0, "trajectory": 10.0, "cross_camera": 5.0, "vehicle": 5.0, "behaviour": 0.0},
        night_start_time="21:00",
        night_end_time="04:00"
    )
    new_cfg = risk_service.update_config(payload)
    assert new_cfg.config_version != curr_cfg.config_version
    assert new_cfg.weights["zone"] == 30.0
    assert new_cfg.night_start_time == "21:00"

    # Summary check
    summary = risk_service.get_risk_summary()
    assert summary.active_config_version == new_cfg.config_version
