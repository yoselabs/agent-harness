"""
Conftest package.json check.

WHAT: Runs conftest on package.json with bundled JavaScript policies to enforce
engines field, ESM type, and version hygiene.

WHY: Agents create package.json files missing critical fields (engines, type)
and use wildcard versions. These misconfigurations cause "works on my machine"
failures and non-deterministic dependency resolution.

WITHOUT IT: Node version mismatches in CI/deploy, mixed ESM/CJS module errors,
different dependency versions on every npm install.

FIX: Run `agent-harness lint` to see specific package.json issues.

REQUIRES: conftest (via PATH)
"""

from __future__ import annotations

from pathlib import Path

from agent_harness.conftest import run_conftest as _run_conftest
from agent_harness.runner import CheckResult


def run_conftest_package(project_dir: Path) -> CheckResult:
    """Run conftest on package.json with bundled javascript policies."""
    return _run_conftest(
        "conftest-package",
        project_dir,
        "package.json",
        "javascript",
    )
