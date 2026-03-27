"""pip-audit runner — parse output and produce AuditFindings."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agent_harness.security.models import AuditFinding


def run_pip_audit(project_dir: Path) -> str | None:
    """Run pip-audit and return JSON output, or None if tool unavailable."""
    for cmd in [
        ["uvx", "pip-audit", "--format=json", "--output=-"],
        ["pip-audit", "--format=json", "--output=-"],
    ]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=120,
            )
            if result.stdout:
                return result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def parse_pip_audit_output(output: str, new_deps: set[str]) -> list[AuditFinding]:
    """Parse pip-audit JSON output into AuditFindings."""
    data = json.loads(output)
    findings: list[AuditFinding] = []

    for dep in data.get("dependencies", []):
        pkg_name = dep["name"].lower().replace("_", "-")
        version = dep["version"]
        is_new = pkg_name in new_deps

        for vuln in dep.get("vulns", []):
            findings.append(
                AuditFinding(
                    package=dep["name"],
                    version=version,
                    vuln_id=vuln["id"],
                    severity="unknown",
                    description=vuln.get("description", ""),
                    fix_versions=vuln.get("fix_versions", []),
                    is_new_dep=is_new,
                )
            )

    return findings
