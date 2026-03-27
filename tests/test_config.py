import subprocess

from agent_harness.config import load_config


def test_load_config_from_file(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text(
        "stacks: [python, docker]\npython:\n  coverage_threshold: 90\n"
    )
    config = load_config(tmp_path)
    assert "python" in config["stacks"]
    assert config["python"]["coverage_threshold"] == 90


def test_load_config_defaults(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    config = load_config(tmp_path)
    assert "python" in config["stacks"]


def test_load_config_with_exclude(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text(
        "stacks: [python]\nexclude:\n  - _archive/\n  - vendor/\n"
    )
    config = load_config(tmp_path)
    assert "_archive/" in config["exclude"]
    assert "vendor/" in config["exclude"]


def test_load_config_exclude_defaults_empty(tmp_path):
    config = load_config(tmp_path)
    assert config["exclude"] == []


def test_load_config_disable_stack(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    (tmp_path / ".agent-harness.yml").write_text("stacks: [docker]\n")
    config = load_config(tmp_path)
    assert "python" not in config["stacks"]


def test_load_config_javascript(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    (tmp_path / ".agent-harness.yml").write_text(
        "stacks: [javascript]\njavascript:\n  coverage_threshold: 90\n"
    )
    config = load_config(tmp_path)
    assert "javascript" in config["stacks"]
    assert config["javascript"]["coverage_threshold"] == 90


def test_load_config_javascript_defaults(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    config = load_config(tmp_path)
    assert "javascript" in config["stacks"]


def test_load_config_malformed_yaml(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text("stacks: [python\n  bad yaml")
    config = load_config(tmp_path)
    # Should fall back to defaults without crashing
    assert config["exclude"] == []


def test_load_config_passthrough_sections(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text(
        "stacks: [docker]\ndocker:\n  own_image_prefix: ghcr.io/myorg/\n"
    )
    config = load_config(tmp_path)
    assert config["docker"]["own_image_prefix"] == "ghcr.io/myorg/"


def test_load_config_git_root_resolved(tmp_path):
    """Config includes git_root when inside a git repo."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    config = load_config(tmp_path)
    assert config["git_root"] == tmp_path


def test_load_config_git_root_none_outside_repo(tmp_path):
    """Config git_root is None when not inside a git repo."""
    config = load_config(tmp_path)
    assert config["git_root"] is None


def test_load_config_git_root_subdir(tmp_path):
    """Config git_root points to repo root even from a subdirectory."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
    subdir = tmp_path / "services" / "api"
    subdir.mkdir(parents=True)
    config = load_config(subdir)
    assert config["git_root"] == tmp_path
