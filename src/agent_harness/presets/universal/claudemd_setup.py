"""
CLAUDE.md workflow instructions check for init.

WHAT: Verifies that an existing CLAUDE.md contains key workflow instructions
(make check, make lint, agent-harness lint, agent-harness fix) that AI agents
need for daily operation.

WHY: Without workflow instructions in CLAUDE.md, AI agents don't know about
quality gates like `make check`. They may skip tests, coverage-diff, or
security-audit because the commands aren't documented where they look first.

FIX: Run the agent-harness skill to audit CLAUDE.md and add targeted
workflow instructions that fit the existing document style. Not auto-fixable
because it requires AI judgment to integrate naturally.
"""

from __future__ import annotations

from pathlib import Path

from agent_harness.setup_check import SetupIssue

# Key phrases that indicate the CLAUDE.md has workflow instructions.
_GATE_PHRASES = ["make check", "make lint", "agent-harness lint", "agent-harness fix"]
_FULL_GATE_PHRASES = ["make check"]


def check_claudemd_setup(project_dir: Path) -> list[SetupIssue]:
    """Check CLAUDE.md for presence of key workflow instructions."""
    claudemd_path = project_dir / "CLAUDE.md"
    if not claudemd_path.exists():
        return []  # Scaffold will create it

    content = claudemd_path.read_text().lower()

    has_full_gate = any(phrase in content for phrase in _FULL_GATE_PHRASES)
    has_any_lint = any(phrase in content for phrase in _GATE_PHRASES)

    if has_full_gate and has_any_lint:
        return []  # Looks good

    if has_any_lint and not has_full_gate:
        return [
            SetupIssue(
                file="CLAUDE.md",
                message=(
                    "CLAUDE.md should mention `make check` as the full quality gate "
                    "(lint + test + security-audit)"
                ),
                severity="recommendation",
            )
        ]

    # Has CLAUDE.md but no workflow instructions at all
    return [
        SetupIssue(
            file="CLAUDE.md",
            message=(
                "exists but missing workflow instructions — "
                "run the agent-harness skill to audit and add dev commands"
            ),
            severity="recommendation",
        )
    ]
