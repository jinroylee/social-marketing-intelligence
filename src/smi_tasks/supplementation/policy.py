"""Exact human target and operator-owned value policy for one missing profile field."""

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from smi_ingestion.evidence import EvidenceError


@dataclass(frozen=True)
class ProfileSupplement:
    """Explicit supplied profile reference and expected stable ID; handles grant no identity."""

    profile_url: str
    native_id: str

    def validate(self) -> None:
        """Require one canonical direct profile URL and a numeric native identity."""
        try:
            parsed = urlsplit(self.profile_url)
            valid = (isinstance(self.native_id, str) and re.fullmatch(r'[0-9]{1,30}', self.native_id)
                and parsed.scheme == 'https' and parsed.netloc == 'www.tiktok.com'
                and re.fullmatch(r'/@[A-Za-z0-9._]{1,64}', parsed.path)
                and not parsed.query and not parsed.fragment)
        except (TypeError, ValueError, AttributeError):
            valid = False
        if not valid:
            raise EvidenceError('invalid_profile_supplement_scope')


@dataclass(frozen=True)
class SupplementationPolicy:
    """Trusted nickname-fill policy; value points are configured estimates, not source truth.

    The sole supported secondary capability is a profile-only Bright Data read.
    Other configured route names report unavailable capability without fallback.
    """

    version: str = 'missing-nickname-v1'
    field: str = 'nickname'
    route: str = 'brightdata-tiktok-profile'
    max_capture_age_seconds: int = 86400
    expected_information_value: int = 1
    minimum_information_value: int = 1

    def validate(self) -> None:
        """Validate finite operator estimates and the sole field before pinning approval."""
        if (self.field != 'nickname' or not isinstance(self.version, str) or not 1 <= len(self.version) <= 100
                or not isinstance(self.route, str) or not 1 <= len(self.route) <= 100
                or any(type(v) is not int or not 0 <= v <= 31_536_000 for v in (
                    self.max_capture_age_seconds, self.expected_information_value, self.minimum_information_value))):
            raise EvidenceError('invalid_supplementation_policy')
