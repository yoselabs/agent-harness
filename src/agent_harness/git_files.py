"""Git-aware file discovery -- respects .gitignore, finds tracked + untracked files."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path


def find_files(project_dir: Path, patterns: list[str]) -> list[Path]:
    """Find files matching glob patterns, respecting .gitignore.

    Uses git ls-files for repos (tracked + untracked, excluding ignored).
    Falls back to filesystem walk for non-git directories.
    """
    files = _git_find(project_dir, patterns)
    if files is not None:
        return files
    return _fs_find(project_dir, patterns)


def _git_find(project_dir: Path, patterns: list[str]) -> list[Path] | None:
    """Use git ls-files to find files. Returns None if not in a git repo."""
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            *patterns,
        ],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if result.returncode != 0:
        return None
    paths = []
    for line in result.stdout.strip().splitlines():
        if line:
            paths.append((project_dir / line).resolve())
    return sorted(set(paths))


def _fs_find(project_dir: Path, patterns: list[str]) -> list[Path]:
    """Fallback: filesystem walk with basic glob matching."""
    _skip = {
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
    results: set[Path] = set()
    for path in project_dir.rglob("*"):
        if any(part in _skip for part in path.parts):
            continue
        if not path.is_file():
            continue
        rel = str(path.relative_to(project_dir))
        if any(
            fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(path.name, p) for p in patterns
        ):
            results.add(path.resolve())
    return sorted(results)
