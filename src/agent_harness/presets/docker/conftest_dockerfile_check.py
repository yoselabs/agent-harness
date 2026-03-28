"""
Conftest Dockerfile check.

WHAT: Runs conftest on all Dockerfiles with bundled policies covering base image
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


def run_conftest_dockerfile(
    project_dir: Path,
    dockerfiles: list[Path] | None = None,
    conftest_skip: dict[str, list[str]] | None = None,
) -> list[CheckResult]:
    """Run conftest on Dockerfiles with bundled dockerfile policies.

    Args:
        project_dir: Project root directory.
        dockerfiles: Relative paths to Dockerfiles. If None, checks project_dir/Dockerfile.
        conftest_skip: Map of relative Dockerfile path -> list of policy IDs to skip.
    """
    if conftest_skip is None:
        conftest_skip = {}

    if dockerfiles is None:
        skip = conftest_skip.get("Dockerfile", [])
        data = {"exceptions": skip} if skip else None
        return [
            _run_conftest(
                "conftest-dockerfile",
                project_dir,
                "Dockerfile",
                "dockerfile",
                data=data,
            )
        ]

    if not dockerfiles:
        return [
            CheckResult(
                name="conftest-dockerfile", passed=True, output="No Dockerfiles found"
            )
        ]

    results = []
    for rel_path in dockerfiles:
        skip = conftest_skip.get(str(rel_path), [])
        data = {"exceptions": skip} if skip else None
        name = (
            f"conftest-dockerfile:{rel_path}"
            if str(rel_path) != "Dockerfile"
            else "conftest-dockerfile"
        )
        results.append(
            _run_conftest(name, project_dir, str(rel_path), "dockerfile", data=data)
        )
    return results
