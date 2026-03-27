from unittest.mock import patch

from agent_harness.security.audit import run_security_audit
from agent_harness.security.models import AuditFinding, SecurityReport


def test_audit_python_project(tmp_path):
    """Python project with pip-audit findings."""
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["requests"]\n')

    mock_findings = [
        AuditFinding(
            package="requests",
            version="2.25.0",
            vuln_id="CVE-2026-1234",
            severity="high",
            description="bad",
            fix_versions=["2.25.1"],
            is_new_dep=False,
        ),
    ]

    with (
        patch(
            "agent_harness.security.audit.run_pip_audit",
            return_value='{"dependencies":[],"fixes":[]}',
        ),
        patch(
            "agent_harness.security.audit.parse_pip_audit_output",
            return_value=mock_findings,
        ),
        patch("agent_harness.security.audit.detect_new_deps", return_value=set()),
    ):
        report = run_security_audit(tmp_path, stacks={"python"}, config={})

    assert isinstance(report, SecurityReport)
    assert len(report.findings) == 1


def test_audit_no_stacks(tmp_path):
    """No stacks detected — empty report."""
    report = run_security_audit(tmp_path, stacks=set(), config={})
    assert isinstance(report, SecurityReport)
    assert report.findings == []


def test_audit_tool_unavailable(tmp_path):
    """Audit tool not installed — empty report with no crash."""
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["requests"]\n')

    with (
        patch("agent_harness.security.audit.run_pip_audit", return_value=None),
        patch("agent_harness.security.audit.detect_new_deps", return_value=set()),
    ):
        report = run_security_audit(tmp_path, stacks={"python"}, config={})

    assert report.findings == []


def test_audit_applies_ignores(tmp_path):
    """Ignored CVEs should be reflected in the report."""
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["requests"]\n')

    mock_findings = [
        AuditFinding(
            "requests",
            "2.25.0",
            "CVE-2026-1234",
            "high",
            "bad",
            ["2.25.1"],
            is_new_dep=True,
        ),
    ]

    config = {"security": {"ignore": [{"id": "CVE-2026-1234", "reason": "known"}]}}

    with (
        patch(
            "agent_harness.security.audit.run_pip_audit",
            return_value='{"dependencies":[],"fixes":[]}',
        ),
        patch(
            "agent_harness.security.audit.parse_pip_audit_output",
            return_value=mock_findings,
        ),
        patch(
            "agent_harness.security.audit.detect_new_deps", return_value={"requests"}
        ),
    ):
        report = run_security_audit(tmp_path, stacks={"python"}, config=config)

    assert report.has_failures is False
    assert report.ignored_count == 1
