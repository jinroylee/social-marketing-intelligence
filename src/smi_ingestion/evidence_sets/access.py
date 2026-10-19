"""Trusted caller context for the local workspace boundary."""

from dataclasses import dataclass
from typing import Literal

from ..evidence import EvidenceError


@dataclass(frozen=True)
class ActorContext:
    """An attributable local caller; construct this at a trusted application boundary."""

    workspace_id: str
    actor_id: str
    kind: Literal["human", "automation"]

    def require_workspace(self, workspace_id: str, *, importing: bool = False) -> None:
        """Reject foreign or invalid contexts; only human operators import snapshots."""
        if (not isinstance(self.actor_id, str) or not self.actor_id.strip()
                or not isinstance(workspace_id, str) or not workspace_id.strip()
                or self.workspace_id != workspace_id
                or self.kind not in {"human", "automation"}
                or (importing and self.kind != "human")):
            raise EvidenceError("workspace_access_denied")
