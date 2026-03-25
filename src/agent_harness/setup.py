"""Setup check framework — diagnose + fix for init command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class SetupIssue:
    """A single issue found by a setup check."""

    file: str
    message: str
    severity: str  # "critical" | "recommendation"
    fix: Callable[[Path], None] | None = None

    @property
    def fixable(self) -> bool:
        return self.fix is not None
