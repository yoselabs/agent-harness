"""Tests for Python preset setup checks."""

from __future__ import annotations

from pathlib import Path

from agent_harness.presets.python.setup import check_python_setup


def _write_pyproject(tmp_path: Path, content: str) -> Path:
    """Write a pyproject.toml and return the project dir."""
    (tmp_path / "pyproject.toml").write_text(content)
    return tmp_path


def test_missing_cov_fail_under(tmp_path):
    """Missing --cov-fail-under → critical + fixable."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov"
""",
    )
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    assert len(cov_issues) == 1
    assert cov_issues[0].severity == "critical"
    assert cov_issues[0].fixable


def test_missing_cov_fail_under_fix_applies(tmp_path):
    """Fix adds --cov-fail-under=95 to addopts."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov"
""",
    )
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    assert cov_issues[0].fix is not None
    cov_issues[0].fix(tmp_path)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "--cov-fail-under=95" in content
    assert "--strict-markers" in content
    assert "--cov" in content


def test_low_threshold_recommendation(tmp_path):
    """Threshold 50% → recommendation (not critical, above 30%)."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=50"
""",
    )
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    assert len(cov_issues) == 1
    assert cov_issues[0].severity == "recommendation"
    assert not cov_issues[0].fixable


def test_missing_verbose_flag(tmp_path):
    """Missing -v → critical + fixable."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "--strict-markers --cov --cov-fail-under=95"
""",
    )
    issues = check_python_setup(tmp_path)
    v_issues = [i for i in issues if "-v" in i.message]
    assert len(v_issues) == 1
    assert v_issues[0].severity == "critical"
    assert v_issues[0].fixable


def test_missing_verbose_fix_applies(tmp_path):
    """Fix adds -v to addopts."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "--strict-markers --cov --cov-fail-under=95"
""",
    )
    issues = check_python_setup(tmp_path)
    v_issues = [i for i in issues if "-v" in i.message]
    assert v_issues[0].fix is not None
    v_issues[0].fix(tmp_path)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "-v" in content


def test_good_config_no_issues(tmp_path):
    """Well-configured project → no issues."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = true

[tool.coverage.run]
branch = true
""",
    )
    issues = check_python_setup(tmp_path)
    assert issues == []


def test_no_pyproject_no_issues(tmp_path):
    """No pyproject.toml → empty list (nothing to check)."""
    issues = check_python_setup(tmp_path)
    assert issues == []


def test_missing_skip_covered(tmp_path):
    """Missing skip_covered → critical + fixable."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = false

[tool.coverage.run]
branch = true
""",
    )
    issues = check_python_setup(tmp_path)
    skip_issues = [i for i in issues if "skip_covered" in i.message]
    assert len(skip_issues) == 1
    assert skip_issues[0].severity == "critical"
    assert skip_issues[0].fixable


def test_missing_branch_coverage(tmp_path):
    """Missing branch coverage → critical + fixable."""
    _write_pyproject(
        tmp_path,
        """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = true
""",
    )
    issues = check_python_setup(tmp_path)
    branch_issues = [i for i in issues if "branch" in i.message]
    assert len(branch_issues) == 1
    assert branch_issues[0].severity == "critical"
    assert branch_issues[0].fixable
