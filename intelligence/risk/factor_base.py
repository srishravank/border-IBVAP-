from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class RiskFactorResult:
    """
    Standardized result emitted by each individual risk factor.
    Guarantees full explainability, traceable evidence, and confidence rating.
    """
    factor_type: str                   # e.g., ZONE_SENSITIVITY, FENCE_CROSSING, etc.
    factor_name: str                   # Human-readable title
    raw_score: float                   # Unweighted score in [0.0, 1.0] representing factor intensity
    contribution: float = 0.0          # Weighted contribution score calculated by aggregator
    confidence: float = 1.0            # Confidence in this specific factor assessment [0.0, 1.0]
    evidence: str = ""                 # Precise human-readable explanation of why this factor contributed
    source_event_ids: List[str] = field(default_factory=list)  # Traceable underlying event IDs
    metadata: Dict[str, Any] = field(default_factory=dict)     # Machine-readable diagnostic metadata
    is_available: bool = True          # True if factor was successfully evaluated, False if missing/disabled


class BaseRiskFactor(ABC):
    """
    Abstract base class for all modular Risk Factors in IBVAP 2.0.
    Ensures decoupled factor evaluation and graceful failure isolation.
    """

    @property
    @abstractmethod
    def factor_type(self) -> str:
        """Unique identifier for the factor (e.g., 'ZONE_SENSITIVITY')."""
        pass

    @property
    @abstractmethod
    def default_weight(self) -> float:
        """Default weight points assigned to this factor."""
        pass

    @abstractmethod
    def evaluate(self, incident_context: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> RiskFactorResult:
        """
        Evaluates the factor against verified incident context.
        
        Args:
            incident_context: Dictionary containing:
                - incident: IncidentModel or dict
                - subject: SubjectModel or dict
                - events: List of SecurityEventModel or dicts
                - zones: Dict of zone_id -> ZoneModel or dicts
                - journey: List of SubjectTrackLinkModel or steps
                - associated_vehicles: List of AssociatedVehicleModel or dicts
                - topology: CameraTopologyGraph
            config: Optional factor-specific configuration overrides
            
        Returns:
            RiskFactorResult with raw_score, confidence, evidence, and source_event_ids.
        """
        pass
