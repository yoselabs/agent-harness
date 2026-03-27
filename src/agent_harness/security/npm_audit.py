"""npm-audit runner — parse output and produce AuditFindings."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agent_harness.security.models import AuditFinding


def run_npm_audit(project_dir: Path) -> str | None:
    """Run npm audit and return JSON output, or None if tool unavailable."""
    try:
        result = subprocess.run(
            ["npm", "audit", "--json"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=120,
        )
        if result.stdout:
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def parse_npm_audit_output(output: str, new_deps: set[str]) -> list[AuditFinding]:
    """Parse npm audit JSON output into AuditFindings."""
    data = json.loads(output)
    findings: list[AuditFinding] = []

    for pkg_name, vuln_data in data.get("vulnerabilities", {}).items():
        via_entries = vuln_data.get("via", [])
        direct_vulns = [v for v in via_entries if isinstance(v, dict)]
        if not direct_vulns:
            continue

        severity = vuln_data.get("severity", "unknown")
        if severity == "moderate":
            severity = "medium"

        is_new = pkg_name in new_deps
        fix_available = vuln_data.get("fixAvailable", False)

        for vuln in direct_vulns:
            findings.append(
                AuditFinding(
                    package=pkg_name,
                    version="",
                    vuln_id=f"npm-{vuln.get('source', 'unknown')}",
                    severity=severity,
                    description=vuln.get("title", ""),
                    fix_versions=["fix available"] if fix_available else [],
                    is_new_dep=is_new,
                )
            )

    return findings
