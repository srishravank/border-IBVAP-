import pytest
from datetime import datetime, timezone
from intelligence.risk.risk_aggregator import RiskAggregator
from intelligence.risk.explanation_generator import ExplanationGenerator


def test_risk_aggregator_weighted_scoring_and_normalization():
    aggregator = RiskAggregator()

    # Create dummy incident context
    night_dt = datetime(2026, 9, 20, 23, 0, tzinfo=timezone.utc)
    incident_context = {
        "incident": {"incident_id": "INC-TEST-001", "subject_id": "SUBJ-TEST-001", "created_at": night_dt},
        "subject": {"subject_id": "SUBJ-TEST-001", "total_cameras_visited": 3},
        "events": [
            {
                "event_id": "EVT-T1",
                "event_type": "ZONE_INTRUSION",
                "zone_id": "Z1",
                "zone_name": "Perimeter Fence",
                "status": "CONFIRMED",
                "confidence": 0.95,
                "created_at": night_dt,
                "trajectory": [[100.0, 100.0], [150.0, 150.0], [200.0, 200.0], [250.0, 250.0]]
            }
        ],
        "zones": {
            "Z1": {"sensitivity": "high", "zone_type": "restricted"}
        },
        "journey": [
            {"camera_id": "CAM-01", "match_status": "CONFIRMED_LINK", "match_score": 1.0, "first_timestamp": night_dt},
            {"camera_id": "CAM-02", "match_status": "CONFIRMED_LINK", "match_score": 0.92, "first_timestamp": night_dt},
            {"camera_id": "CAM-03", "match_status": "CONFIRMED_LINK", "match_score": 0.89, "first_timestamp": night_dt}
        ],
        "associated_vehicles": [
            {"vehicle_subject_id": "VEH-001", "camera_id": "CAM-02", "proximity_meters": 5.0}
        ]
    }

    assessment = aggregator.assess_incident(incident_context)

    # Validate output structure
    assert assessment.incident_id == "INC-TEST-001"
    assert assessment.subject_id == "SUBJ-TEST-001"
    assert 0.0 <= assessment.score <= 100.0
    assert assessment.risk_level == "HIGH"
    assert assessment.confidence >= 0.8
    assert len(assessment.factors) == 7
    assert len(assessment.evidence_checklist) >= 5

    # Validate explanation contains key clauses
    assert "HIGH" in assessment.explanation
    assert "Score:" in assessment.explanation


def test_risk_aggregator_low_risk_scenario():
    aggregator = RiskAggregator()
    day_dt = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)

    incident_context = {
        "incident": {"incident_id": "INC-LOW", "subject_id": "SUBJ-LOW", "created_at": day_dt},
        "subject": {"subject_id": "SUBJ-LOW", "total_cameras_visited": 1},
        "events": [],
        "zones": {},
        "journey": [{"camera_id": "CAM-01", "match_status": "CONFIRMED_LINK", "match_score": 1.0, "first_timestamp": day_dt}],
        "associated_vehicles": []
    }

    assessment = aggregator.assess_incident(incident_context)
    assert assessment.score <= 30.0
    assert assessment.risk_level == "LOW"
    assert "No verified high-risk boundary" in assessment.explanation


def test_explanation_generator():
    checklist = ExplanationGenerator.generate_evidence_checklist([])
    assert isinstance(checklist, list)
