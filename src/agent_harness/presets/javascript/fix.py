"""JavaScript auto-fix: biome check --fix."""

from __future__ import annotations

from pathlib import Path

from agent_harness.runner import run_check


def run_javascript_fix(project_dir: Path) -> list[str]:
    """Auto-fix JavaScript issues with biome. Returns list of actions taken."""
    from .biome_check import _biome_prefix, BIOME_VCS_FLAGS

    actions = []
    biome_cmd = _biome_prefix() + ["check", "--fix", "."] + BIOME_VCS_FLAGS

    result = run_check("biome:fix", biome_cmd, cwd=str(project_dir))
    if result.passed:
        actions.append("biome: auto-fixed lint and format issues")
    elif "not found" in result.error.lower():
        actions.append("biome: not installed, skipping fix")

    return actions
