"""Conftest pyproject.toml check — uses shared conftest runner."""

from __future__ import annotations

from pathlib import Path

from agent_harness.conftest import run_conftest
from agent_harness.runner import CheckResult


def run_conftest_python(project_dir: Path) -> CheckResult:
    """Run conftest on pyproject.toml with bundled python policies."""
    return run_conftest(
        "conftest-python",
        project_dir,
        "pyproject.toml",
        "python",
    )
