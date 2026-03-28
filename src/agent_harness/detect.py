"""Stack detection orchestrator — delegates to preset detect methods."""

from __future__ import annotations

from pathlib import Path

from agent_harness.git_files import find_files
from agent_harness.registry import PRESETS

# Dependency manifests that define a real project (not just a build target)
_PROJECT_MANIFESTS = [
    "pyproject.toml",
    "package.json",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "pom.xml",
    "build.gradle",
]


def detect_stacks(project_dir: Path) -> set[str]:
    """Detect which stacks a project uses based on file presence."""
    return {p.name for p in PRESETS if p.detect(project_dir)}


def detect_all(project_dir: Path) -> dict[Path, set[str]]:
    """Detect stacks in root and subdirectories.

    A directory is a project only if it has a dependency manifest
    (pyproject.toml, package.json, etc.) or is the root directory.
    Docker-only directories are build targets, not projects.
    """
    all_patterns = [f"**/{m}" for m in _PROJECT_MANIFESTS] + [
        m for m in _PROJECT_MANIFESTS
    ]
    manifest_files = find_files(project_dir, all_patterns)

    project_dirs: set[Path] = set()
    for f in manifest_files:
        project_dirs.add(f.parent)

    root_stacks = detect_stacks(project_dir)
    if root_stacks:
        project_dirs.add(project_dir)

    results: dict[Path, set[str]] = {}
    for d in sorted(project_dirs):
        stacks = detect_stacks(d)
        if stacks:
            results[d] = stacks

    return results
