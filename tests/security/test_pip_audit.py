import json

from agent_harness.security.pip_audit import parse_pip_audit_output


def test_parse_empty_output():
    """No vulnerabilities found."""
    output = json.dumps({"dependencies": [], "fixes": []})
    findings = parse_pip_audit_output(output, new_deps=set())
    assert findings == []


def test_parse_vulnerabilities():
    """Parse pip-audit JSON with vulnerabilities."""
    output = json.dumps(
        {
            "dependencies": [
                {
                    "name": "requests",
                    "version": "2.25.0",
                    "vulns": [
                        {
                            "id": "PYSEC-2026-1",
                            "fix_versions": ["2.25.1"],
                            "aliases": ["CVE-2026-1234"],
                            "description": "SSRF vulnerability",
                        }
                    ],
                },
                {
                    "name": "flask",
                    "version": "2.0.0",
                    "vulns": [],
                },
            ],
            "fixes": [],
        }
    )
    findings = parse_pip_audit_output(output, new_deps={"requests"})
    assert len(findings) == 1
    assert findings[0].package == "requests"
    assert findings[0].vuln_id == "PYSEC-2026-1"
    assert findings[0].fix_versions == ["2.25.1"]
    assert findings[0].is_new_dep is True


def test_parse_existing_dep_not_new():
    """Existing dep vulnerabilities should have is_new_dep=False."""
    output = json.dumps(
        {
            "dependencies": [
                {
                    "name": "urllib3",
                    "version": "1.26.0",
                    "vulns": [
                        {
                            "id": "CVE-2026-9999",
                            "fix_versions": [],
                            "aliases": [],
                            "description": "Something",
                        }
                    ],
                },
            ],
            "fixes": [],
        }
    )
    findings = parse_pip_audit_output(output, new_deps={"requests"})
    assert len(findings) == 1
    assert findings[0].is_new_dep is False


def test_parse_severity_from_aliases():
    """pip-audit doesn't include severity — default to 'unknown'."""
    output = json.dumps(
        {
            "dependencies": [
                {
                    "name": "pkg",
                    "version": "1.0",
                    "vulns": [
                        {
                            "id": "GHSA-xxxx",
                            "fix_versions": ["1.1"],
                            "aliases": ["CVE-2026-5555"],
                            "description": "Bad stuff",
                        }
                    ],
                },
            ],
            "fixes": [],
        }
    )
    findings = parse_pip_audit_output(output, new_deps=set())
    assert findings[0].severity == "unknown"
