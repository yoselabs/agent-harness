from datetime import date

from agent_harness.security.config import load_security_config


def test_empty_config():
    config = load_security_config({})
    assert config.ignored_cves == set()
    assert config.base_branch == "origin/main"


def test_ignore_list():
    config = load_security_config(
        {
            "security": {
                "ignore": [
                    {
                        "id": "CVE-2025-1111",
                        "reason": "No fix",
                        "expires": "2026-12-31",
                    },
                    {"id": "CVE-2025-2222", "reason": "False positive"},
                ]
            }
        }
    )
    assert config.ignored_cves == {"CVE-2025-1111", "CVE-2025-2222"}


def test_expired_ignore_excluded(monkeypatch):
    """Expired CVE ignores should not be in the set."""
    monkeypatch.setattr(
        "agent_harness.security.config._today", lambda: date(2026, 4, 1)
    )
    config = load_security_config(
        {
            "security": {
                "ignore": [
                    {
                        "id": "CVE-2025-1111",
                        "reason": "No fix",
                        "expires": "2026-03-01",
                    },
                    {
                        "id": "CVE-2025-2222",
                        "reason": "Still valid",
                        "expires": "2026-12-31",
                    },
                ]
            }
        }
    )
    assert config.ignored_cves == {"CVE-2025-2222"}


def test_custom_base_branch():
    config = load_security_config({"security": {"base_branch": "origin/develop"}})
    assert config.base_branch == "origin/develop"


def test_no_expiry_never_expires():
    config = load_security_config(
        {
            "security": {
                "ignore": [
                    {"id": "CVE-2025-9999", "reason": "Permanent ignore"},
                ]
            }
        }
    )
    assert config.ignored_cves == {"CVE-2025-9999"}
