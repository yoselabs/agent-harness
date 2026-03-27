import json

from agent_harness.security.npm_audit import parse_npm_audit_output


def test_parse_empty_output():
    output = json.dumps({"vulnerabilities": {}})
    findings = parse_npm_audit_output(output, new_deps=set())
    assert findings == []


def test_parse_vulnerabilities():
    output = json.dumps(
        {
            "vulnerabilities": {
                "lodash": {
                    "name": "lodash",
                    "severity": "high",
                    "via": [
                        {
                            "source": 1234,
                            "name": "lodash",
                            "title": "Prototype Pollution",
                            "url": "https://ghsa.example",
                            "severity": "high",
                            "cwe": ["CWE-1321"],
                            "range": "<4.17.21",
                        }
                    ],
                    "fixAvailable": True,
                }
            }
        }
    )
    findings = parse_npm_audit_output(output, new_deps={"lodash"})
    assert len(findings) == 1
    assert findings[0].package == "lodash"
    assert findings[0].severity == "high"
    assert findings[0].is_new_dep is True
    assert len(findings[0].fix_versions) > 0


def test_parse_no_fix_available():
    output = json.dumps(
        {
            "vulnerabilities": {
                "old-pkg": {
                    "name": "old-pkg",
                    "severity": "critical",
                    "via": [{"title": "Bad", "severity": "critical", "source": 1}],
                    "fixAvailable": False,
                }
            }
        }
    )
    findings = parse_npm_audit_output(output, new_deps=set())
    assert len(findings) == 1
    assert findings[0].fix_versions == []
    assert findings[0].is_new_dep is False


def test_parse_via_string_skipped():
    """When 'via' contains a string (transitive), skip it — only direct vulns."""
    output = json.dumps(
        {
            "vulnerabilities": {
                "transitive-pkg": {
                    "name": "transitive-pkg",
                    "severity": "moderate",
                    "via": ["some-other-pkg"],
                    "fixAvailable": True,
                }
            }
        }
    )
    findings = parse_npm_audit_output(output, new_deps=set())
    assert findings == []
