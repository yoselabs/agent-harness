from pathlib import Path

from agent_harness.presets.universal.claudemd_setup import check_claudemd_setup


def test_no_claudemd_returns_no_issues(tmp_path: Path):
    """No CLAUDE.md at all — scaffold will create it, no setup issue needed."""
    issues = check_claudemd_setup(tmp_path)
    assert issues == []


def test_claudemd_exists_returns_recommendation(tmp_path: Path):
    """Existing CLAUDE.md should get a recommendation to audit via skill."""
    (tmp_path / "CLAUDE.md").write_text("# My Project\n\nSome custom instructions.\n")
    issues = check_claudemd_setup(tmp_path)
    assert len(issues) == 1
    assert issues[0].severity == "recommendation"
    assert "skill" in issues[0].message.lower() or "audit" in issues[0].message.lower()
    assert issues[0].fix is None  # Not auto-fixable — needs AI judgment


def test_claudemd_with_make_check_returns_no_issues(tmp_path: Path):
    """CLAUDE.md that already mentions make check — no issue."""
    (tmp_path / "CLAUDE.md").write_text(
        "# My Project\n\n## Dev Commands\n\nmake check\nmake lint\n"
    )
    issues = check_claudemd_setup(tmp_path)
    assert issues == []


def test_claudemd_with_agent_harness_lint_returns_no_issues(tmp_path: Path):
    """CLAUDE.md mentioning agent-harness lint is also fine."""
    (tmp_path / "CLAUDE.md").write_text(
        "# My Project\n\nRun `agent-harness lint` before committing.\n"
        "Run `make check` for full gate.\n"
    )
    issues = check_claudemd_setup(tmp_path)
    assert issues == []


def test_claudemd_with_lint_but_no_check(tmp_path: Path):
    """CLAUDE.md mentions lint but not the full check gate — recommend adding."""
    (tmp_path / "CLAUDE.md").write_text(
        "# My Project\n\nRun `make lint` before committing.\n"
    )
    issues = check_claudemd_setup(tmp_path)
    assert len(issues) == 1
    assert issues[0].severity == "recommendation"
    assert (
        "make check" in issues[0].message.lower()
        or "workflow" in issues[0].message.lower()
    )
