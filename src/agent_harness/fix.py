from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from agent_harness.config import load_config
from agent_harness.registry import PRESETS, UNIVERSAL
from agent_harness.workspace import discover_roots


def run_fix(project_dir: Path) -> list[str]:
    """Auto-fix what's fixable, then return actions taken."""
    config = load_config(project_dir)
    actions = UNIVERSAL.run_fix(project_dir, config)
    for preset in PRESETS:
        if preset.name in config.get("stacks", set()):
            actions.extend(preset.run_fix(project_dir, config))
    return actions


def run_fix_all(project_dir: Path) -> dict[Path, list[str]]:
    """Discover all subprojects and run fix in each."""
    roots = discover_roots(project_dir)
    if not roots:
        return {project_dir: run_fix(project_dir)}

    results: dict[Path, list[str]] = {}
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(run_fix, root): root for root in roots}
        for future in as_completed(futures):
            root = futures[future]
            try:
                results[root] = future.result()
            except Exception as e:
                results[root] = [f"error: {e}"]
    return results
