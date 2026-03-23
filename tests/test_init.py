# tests/test_init.py
from agent_harness.init.scaffold import scaffold_project


def test_scaffold_creates_files(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, yes=True)
    assert (tmp_path / ".agent-harness.yml").exists()
    assert (tmp_path / ".yamllint.yml").exists()
    assert (tmp_path / ".pre-commit-config.yaml").exists()
    assert any("CREATE" in a for a in actions)


def test_scaffold_skips_existing(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text("stacks: [python]")
    actions = scaffold_project(tmp_path, yes=True)
    assert any("SKIP" in a and ".agent-harness.yml" in a for a in actions)
    # Shouldn't overwrite
    assert (tmp_path / ".agent-harness.yml").read_text() == "stacks: [python]"


def test_scaffold_creates_makefile(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    scaffold_project(tmp_path, yes=True)
    assert (tmp_path / "Makefile").exists()
    content = (tmp_path / "Makefile").read_text()
    assert "agent-harness lint" in content
    assert "pytest" in content


def test_scaffold_makefile_js_test_command(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    scaffold_project(tmp_path, yes=True)
    content = (tmp_path / "Makefile").read_text()
    assert "npm test" in content


def test_scaffold_skips_existing_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("custom: echo hi")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, yes=True)
    assert "SKIP  Makefile" in " ".join(actions)
    assert (tmp_path / "Makefile").read_text() == "custom: echo hi"


def test_scaffold_cancelled_without_yes(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    monkeypatch.setattr("click.confirm", lambda *a, **kw: False)
    actions = scaffold_project(tmp_path, yes=False)
    assert "Cancelled" in actions
    assert not (tmp_path / ".agent-harness.yml").exists()
