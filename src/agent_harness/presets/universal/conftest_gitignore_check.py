"""
Conftest .gitignore check.

WHAT: Runs conftest on .gitignore with bundled gitignore policies to ensure
secrets and artifacts are excluded from version control, conditional on
detected stacks.

WHY: Agents create .env files with real secrets during development and commit
them. Stack-specific artifacts (.venv, node_modules) bloat the repo. Without
stack awareness, Python entries get flagged on JS projects (false positives)
and JS entries get missed on JS projects (false negatives).

WITHOUT IT: Secrets in git history, false positive noise on wrong stacks,
missing entries for detected stacks.

FIX: Add the reported entries to .gitignore.

REQUIRES: conftest (via PATH)
"""

from __future__ import annotations

from pathlib import Path

from agent_harness.conftest import run_conftest as _run_conftest
from agent_harness.runner import CheckResult


def run_conftest_gitignore(
    project_dir: Path, stacks: set[str] | None = None
) -> CheckResult:
    """Run conftest on .gitignore with stack-conditional policies."""
    stacks_list = sorted(stacks) if stacks else []
    return _run_conftest(
        "conftest-gitignore",
        project_dir,
        ".gitignore",
        "gitignore",
        data={"stacks": stacks_list},
    )
