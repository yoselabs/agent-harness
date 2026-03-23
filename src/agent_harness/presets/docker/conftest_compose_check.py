"""
Conftest docker-compose check.

WHAT: Runs conftest on docker-compose.prod.yml with bundled compose policies
covering dollar escaping, hostname requirements, image pinning, healthchecks,
restart policies, and port binding safety.

WHY: Agents generate compose files with bare $ in passwords (silently corrupted
by interpolation), missing healthchecks (load balancers route to dead containers),
no restart policies (crashed services stay down), and 0.0.0.0 port bindings
(bypasses host firewall, exposes internal services to the internet).

WITHOUT IT: Passwords silently corrupted, silent outages from unhealthy containers,
permanent crashes, and accidentally internet-exposed internal services.

FIX: Read the specific conftest violation messages — each maps to a concrete
compose file change (escape $$, add healthcheck, add restart policy, bind to
127.0.0.1).

REQUIRES: conftest (via PATH)
"""

from __future__ import annotations

from pathlib import Path

from agent_harness.conftest import run_conftest as _run_conftest
from agent_harness.runner import CheckResult


def run_conftest_compose(project_dir: Path, own_image_prefix: str = "") -> CheckResult:
    """Run conftest on docker-compose.prod.yml with bundled compose policies."""
    data = None
    if own_image_prefix:
        data = {"own_image_prefix": own_image_prefix}
    return _run_conftest(
        "conftest-compose",
        project_dir,
        "docker-compose.prod.yml",
        "compose",
        data=data,
    )
