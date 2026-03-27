"""Tests for setup check framework."""

from __future__ import annotations

from pathlib import Path

from agent_harness.setup_check import SetupIssue


def test_setup_issue_critical_with_fix():
    fix_called = []
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under not set",
        severity="critical",
        fix=lambda project_dir: fix_called.append(True),
    )
    assert issue.severity == "critical"
    assert issue.fixable
    assert issue.fix is not None
    issue.fix(Path("/tmp"))
    assert fix_called == [True]


def test_setup_issue_recommendation_no_fix():
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under=50, recommend 90-95%",
        severity="recommendation",
    )
    assert issue.severity == "recommendation"
    assert not issue.fixable


def test_setup_issue_fixable_property():
    fixable = SetupIssue(file="x", message="m", severity="critical", fix=lambda p: None)
    not_fixable = SetupIssue(file="x", message="m", severity="critical")
    assert fixable.fixable is True
    assert not_fixable.fixable is False
