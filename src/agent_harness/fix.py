from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import shutil

from agent_harness.config import load_config
from agent_harness.runner import run_check


def run_fix(project_dir: Path) -> list[str]:
    """Auto-fix what's fixable, then return actions taken."""
    actions = []
    config = load_config(project_dir)

    # Python: ruff fix
    if "python" in config.stacks:
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

    # JavaScript: biome fix
    if "javascript" in config.stacks:
        from agent_harness.stacks.javascript.biome_check import (
            _biome_prefix,
            BIOME_VCS_FLAGS,
        )

        biome_cmd = _biome_prefix() + ["check", "--fix", "."] + BIOME_VCS_FLAGS

        result = run_check("biome:fix", biome_cmd, cwd=str(project_dir))
        if result.passed:
            actions.append("biome: auto-fixed lint and format issues")
        elif "not found" in result.error.lower():
            actions.append("biome: not installed, skipping fix")

    return actions


def run_fix_all(project_dir: Path) -> dict[Path, list[str]]:
    """Discover all subprojects and run fix in each."""
    from agent_harness.workspace import discover_roots

    roots = discover_roots(project_dir)
    if not roots:
        return {project_dir: run_fix(project_dir)}

    all_results: dict[Path, list[str]] = {}
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(run_fix, root): root for root in roots}
        for future in as_completed(futures):
            root = futures[future]
            try:
                all_results[root] = future.result()
            except Exception as e:
                all_results[root] = [f"error: {e}"]
    return all_results
