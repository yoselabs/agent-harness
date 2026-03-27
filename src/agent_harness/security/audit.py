"""Security audit orchestrator — detect stacks, run tools, apply policy."""

from __future__ import annotations

from pathlib import Path

from agent_harness.security.config import load_security_config
from agent_harness.security.dep_diff import detect_new_deps
from agent_harness.security.models import AuditFinding, SecurityReport
from agent_harness.security.npm_audit import parse_npm_audit_output, run_npm_audit
from agent_harness.security.pip_audit import parse_pip_audit_output, run_pip_audit


def run_security_audit(
    project_dir: Path,
    stacks: set[str],
    config: dict,
) -> SecurityReport:
    """Run security audit for all detected stacks."""
    sec_config = load_security_config(config)
    all_findings: list[AuditFinding] = []

    new_deps = detect_new_deps(project_dir, base_branch=sec_config.base_branch)

    if "python" in stacks:
        output = run_pip_audit(project_dir)
        if output is not None:
            all_findings.extend(parse_pip_audit_output(output, new_deps))

    if "javascript" in stacks:
        output = run_npm_audit(project_dir)
        if output is not None:
            all_findings.extend(parse_npm_audit_output(output, new_deps))

    return SecurityReport(
        findings=all_findings,
        ignored_ids=sec_config.ignored_cves,
    )
