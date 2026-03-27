"""
Workspace discovery.

Finds all project roots (directories with .agent-harness.yml) in a repo tree.
Used by lint and fix to run checks across monorepo subprojects.
"""

from __future__ import annotations

from pathlib import Path

SKIP_DIRS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".astro",
    ".next",
    ".nuxt",
    ".worktrees",
    "_archive",
    ".pytest_cache",
    ".ruff_cache",
}


def discover_roots(project_dir: Path, max_depth: int = 4) -> list[Path]:
    """Find directories containing .agent-harness.yml, up to max_depth."""
    roots: list[Path] = []
    _scan(project_dir, roots, depth=0, max_depth=max_depth)
    return sorted(roots)


def _scan(directory: Path, roots: list[Path], depth: int, max_depth: int) -> None:
    if depth > max_depth:
        return
    if (directory / ".agent-harness.yml").exists():
        roots.append(directory)
    try:
        children = sorted(directory.iterdir())
    except PermissionError:
        return
    for child in children:
        if (
            child.is_dir()
            and child.name not in SKIP_DIRS
            and not child.name.startswith(".")
        ):
            _scan(child, roots, depth + 1, max_depth)
