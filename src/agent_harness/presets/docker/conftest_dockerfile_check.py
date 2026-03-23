"""
Conftest Dockerfile check.

WHAT: Runs conftest on Dockerfile with bundled policies covering base image
selection, cache mounts, healthchecks, layer ordering, secrets, and non-root user.

WHY: Agents generate Dockerfiles that run as root, skip healthchecks, use Alpine
with musl-sensitive stacks, hardcode secrets in ENV/ARG, and bust cache by copying
source before dependencies. Each of these is a production incident waiting to happen.

WITHOUT IT: Containers run as root (one exploit = host compromise), orchestrators
can't detect unhealthy containers, 5-minute builds that should take 10 seconds,
and secrets leaked in image layers.

FIX: Read the specific conftest violation messages — each maps to a concrete
Dockerfile change (add USER, add HEALTHCHECK, reorder COPY layers, etc.).

REQUIRES: conftest (via PATH)
"""

from __future__ import annotations

from pathlib import Path

from agent_harness.conftest import run_conftest as _run_conftest
from agent_harness.runner import CheckResult


def run_conftest_dockerfile(project_dir: Path) -> CheckResult:
    """Run conftest on Dockerfile with bundled dockerfile policies."""
    return _run_conftest(
        "conftest-dockerfile",
        project_dir,
        "Dockerfile",
        "dockerfile",
    )
