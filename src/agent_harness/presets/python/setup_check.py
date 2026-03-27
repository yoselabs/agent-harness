"""Python preset setup checks — diagnose + fix pyproject.toml configuration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import tomlkit

from agent_harness.setup_check import SetupIssue


def _load_toml(project_dir: Path) -> dict[str, Any]:
    """Load pyproject.toml as a plain dict for reading."""
    text = (project_dir / "pyproject.toml").read_text()
    return dict(tomlkit.parse(text))


def _patch_toml(project_dir: Path, mutator: Any) -> None:
    """Load pyproject.toml with tomlkit, apply mutator, write back."""
    pyproject_path = project_dir / "pyproject.toml"
    doc = tomlkit.parse(pyproject_path.read_text())
    mutator(doc)
    pyproject_path.write_text(tomlkit.dumps(doc))


def check_python_setup(project_dir: Path) -> list[SetupIssue]:
    """Check pyproject.toml for pytest/coverage configuration issues."""
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    data = _load_toml(project_dir)
    issues: list[SetupIssue] = []

    issues.extend(_check_pytest_addopts(data, project_dir))
    issues.extend(_check_coverage_report(data, project_dir))
    issues.extend(_check_coverage_run(data, project_dir))

    return issues


def _get_addopts(data: dict[str, Any]) -> str | None:
    """Extract addopts string from [tool.pytest.ini_options]."""
    try:
        return data["tool"]["pytest"]["ini_options"]["addopts"]
    except (KeyError, TypeError):
        return None


def _patch_addopts(project_dir: Path, flag: str) -> None:
    """Append a flag to addopts in pyproject.toml, preserving formatting."""

    def mutate(doc: Any) -> None:
        current = doc["tool"]["pytest"]["ini_options"]["addopts"]
        doc["tool"]["pytest"]["ini_options"]["addopts"] = current + " " + flag

    _patch_toml(project_dir, mutate)


def _check_pytest_addopts(data: dict[str, Any], project_dir: Path) -> list[SetupIssue]:
    """Check pytest addopts for required flags."""
    addopts = _get_addopts(data)
    if addopts is None:
        return []  # No pytest config — nothing to check

    issues: list[SetupIssue] = []

    # -v flag
    if "-v" not in addopts:
        issues.append(
            SetupIssue(
                file="pyproject.toml",
                message="addopts missing '-v' — agents need individual test names",
                severity="critical",
                fix=lambda p: _patch_addopts(p, "-v"),
            )
        )

    # --cov-fail-under
    if "--cov-fail-under" not in addopts:
        issues.append(
            SetupIssue(
                file="pyproject.toml",
                message="--cov-fail-under not set — adding with 95%",
                severity="critical",
                fix=lambda p: _patch_addopts(p, "--cov-fail-under=95"),
            )
        )
    else:
        # Extract threshold value
        match = re.search(r"--cov-fail-under=(\d+)", addopts)
        if match:
            threshold = int(match.group(1))
            if 30 <= threshold < 90:
                issues.append(
                    SetupIssue(
                        file="pyproject.toml",
                        message=f"--cov-fail-under={threshold}%, recommend 90-95%",
                        severity="recommendation",
                    )
                )

    return issues


def _check_coverage_report(data: dict[str, Any], project_dir: Path) -> list[SetupIssue]:
    """Check [tool.coverage.report] settings."""
    try:
        report = data["tool"]["coverage"]["report"]
    except (KeyError, TypeError):
        return []

    issues: list[SetupIssue] = []

    if report.get("skip_covered") is not True:

        def fix_skip_covered(p: Path) -> None:
            def mutate(doc: Any) -> None:
                doc["tool"]["coverage"]["report"]["skip_covered"] = True

            _patch_toml(p, mutate)

        issues.append(
            SetupIssue(
                file="pyproject.toml",
                message="coverage.report: skip_covered not true — agents see noise from covered files",
                severity="critical",
                fix=fix_skip_covered,
            )
        )

    return issues


def _check_coverage_run(data: dict[str, Any], project_dir: Path) -> list[SetupIssue]:
    """Check [tool.coverage.run] settings."""
    try:
        run: dict[str, Any] = data["tool"]["coverage"]["run"]
    except (KeyError, TypeError):
        # If coverage.report exists but coverage.run is missing, flag branch
        try:
            data["tool"]["coverage"]["report"]
        except (KeyError, TypeError):
            return []
        run = {}

    issues: list[SetupIssue] = []

    if run.get("branch") is not True:

        def fix_branch(p: Path) -> None:
            def mutate(doc: Any) -> None:
                doc["tool"]["coverage"]["run"]["branch"] = True

            _patch_toml(p, mutate)

        issues.append(
            SetupIssue(
                file="pyproject.toml",
                message="coverage.run: branch not true — line-only coverage misses untested branches",
                severity="critical",
                fix=fix_branch,
            )
        )

    return issues
