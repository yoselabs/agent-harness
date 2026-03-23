"""Python auto-fix: ruff check --fix and ruff format."""

from __future__ import annotations

import shutil
from pathlib import Path

from agent_harness.runner import run_check


def run_python_fix(project_dir: Path) -> list[str]:
    """Auto-fix Python issues with ruff. Returns list of actions taken."""
    actions = []

    if shutil.which("ruff"):
        fix_cmd = ["ruff", "check", "--fix"]
        fmt_cmd = ["ruff", "format"]
    else:
        fix_cmd = ["uv", "run", "ruff", "check", "--fix"]
        fmt_cmd = ["uv", "run", "ruff", "format"]

    # Ruff fix
    result = run_check("ruff:fix", fix_cmd, cwd=str(project_dir))
    if result.passed:
        actions.append("ruff: auto-fixed lint issues")
    elif "not found" in result.error.lower():
        actions.append("ruff: not installed, skipping fix")

    # Ruff format
    result = run_check("ruff:format", fmt_cmd, cwd=str(project_dir))
    if result.passed:
        actions.append("ruff: formatted code")
    elif "not found" in result.error.lower():
        actions.append("ruff: not installed, skipping format")

    return actions
