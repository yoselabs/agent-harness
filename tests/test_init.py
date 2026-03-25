# tests/test_init.py
from agent_harness.init.scaffold import scaffold_project


def test_scaffold_creates_files(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=True)
    assert (tmp_path / ".agent-harness.yml").exists()
    assert (tmp_path / ".yamllint.yml").exists()
    assert (tmp_path / ".pre-commit-config.yaml").exists()
    assert any("CREATE" in a for a in actions)


def test_scaffold_skips_existing(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text("stacks: [python]")
    actions = scaffold_project(tmp_path, apply=True)
    assert any("SKIP" in a and ".agent-harness.yml" in a for a in actions)
    assert (tmp_path / ".agent-harness.yml").read_text() == "stacks: [python]"


def test_scaffold_creates_makefile(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    scaffold_project(tmp_path, apply=True)
    assert (tmp_path / "Makefile").exists()
    content = (tmp_path / "Makefile").read_text()
    assert "agent-harness lint" in content
    assert "pytest" in content


def test_scaffold_makefile_js_test_command(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    scaffold_project(tmp_path, apply=True)
    content = (tmp_path / "Makefile").read_text()
    assert "npm test" in content


def test_scaffold_skips_existing_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("custom: echo hi")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=True)
    assert "SKIP  Makefile" in " ".join(actions)
    assert (tmp_path / "Makefile").read_text() == "custom: echo hi"


def test_report_mode_returns_empty(tmp_path):
    """Without apply, returns empty list (report only)."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=False)
    assert actions == []
    assert not (tmp_path / ".agent-harness.yml").exists()


def test_apply_fixes_pyproject(tmp_path):
    """With apply, fixes are applied to pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("""\
[project]
name = "x"

[tool.pytest.ini_options]
addopts = "--strict-markers --cov"
""")
    actions = scaffold_project(tmp_path, apply=True)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "--cov-fail-under=95" in content
    assert "-v" in content
    assert any("FIXED" in a for a in actions)
