"""Public contract for the BEFORE pre-procedure Gate."""

from .evaluator import evaluate_gate
from .models import (
    Confidence,
    EncounterEvidence,
    Finding,
    FindingStatus,
    GateDecision,
    ProviderEvidence,
    Verdict,
)

__all__ = [
    "Confidence",
    "EncounterEvidence",
    "Finding",
    "FindingStatus",
    "GateDecision",
    "ProviderEvidence",
    "Verdict",
    "evaluate_gate",
]

