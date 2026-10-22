"""Explicit operator freshness and processing configuration."""

from dataclasses import dataclass

from smi_ingestion.evidence import EvidenceError


@dataclass(frozen=True)
class DiscoveryPolicy:
    """Permit avoidance only within a known capture age and exact processing revision.

    The revision names canonical processing policy, not mapper software. No policy
    is implicit: unconfigured discovery keeps retrieving within its hard bounds.
    """

    max_capture_age_seconds: int
    processing_revision: str = 'canonical-v1'

    def validate(self) -> None:
        """Reject unusable age bounds or ambiguous processing versions."""
        if (type(self.max_capture_age_seconds) is not int or not 1 <= self.max_capture_age_seconds <= 31_622_400
                or not isinstance(self.processing_revision, str) or not self.processing_revision.strip()
                or len(self.processing_revision) > 100):
            raise EvidenceError('invalid_discovery_policy')
