"""Tests for git-aware file discovery utility."""

import subprocess
from unittest.mock import patch

from agent_harness.git_files import find_files


def _init_git(path):
    """Initialize a git repo at path."""
    subprocess.run(["git", "init"], cwd=str(path), capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(path),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(path),
        capture_output=True,
    )


def test_find_tracked_files(tmp_path):
    """Finds files that are tracked in git."""
    _init_git(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    subprocess.run(["git", "add", "Dockerfile"], cwd=str(tmp_path), capture_output=True)
    result = find_files(tmp_path, ["Dockerfile"])
    assert result == [tmp_path / "Dockerfile"]


def test_find_untracked_files(tmp_path):
    """Finds untracked files that are not gitignored."""
    _init_git(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    # Not staged, but should still be found
    result = find_files(tmp_path, ["Dockerfile"])
    assert result == [tmp_path / "Dockerfile"]


def test_skips_gitignored_files(tmp_path):
    """Does not find files matching .gitignore patterns."""
    _init_git(tmp_path)
    (tmp_path / ".gitignore").write_text("build/\n")
    subprocess.run(["git", "add", ".gitignore"], cwd=str(tmp_path), capture_output=True)
    build = tmp_path / "build"
    build.mkdir()
    (build / "Dockerfile").write_text("FROM python:3.12")
    result = find_files(tmp_path, ["**/Dockerfile"])
    assert all("build" not in str(p) for p in result)


def test_finds_nested_files(tmp_path):
    """Finds files in subdirectories."""
    _init_git(tmp_path)
    scripts = tmp_path / "scripts" / "autonomy"
    scripts.mkdir(parents=True)
    (scripts / "Dockerfile").write_text("FROM python:3.12")
    (tmp_path / "Dockerfile").write_text("FROM node:22")
    result = find_files(tmp_path, ["**/Dockerfile", "Dockerfile"])
    paths = {str(p.relative_to(tmp_path)) for p in result}
    assert "Dockerfile" in paths
    assert "scripts/autonomy/Dockerfile" in paths


def test_returns_absolute_paths(tmp_path):
    """All returned paths are absolute."""
    _init_git(tmp_path)
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    result = find_files(tmp_path, ["Dockerfile"])
    assert all(p.is_absolute() for p in result)


def test_fallback_without_git(tmp_path):
    """Falls back to filesystem walk when not in a git repo."""
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "Dockerfile").write_text("FROM node:22")
    # Force fallback by making _git_find return None
    with patch("agent_harness.git_files._git_find", return_value=None):
        result = find_files(tmp_path, ["**/Dockerfile", "Dockerfile"])
    assert len(result) >= 2


def test_find_agent_harness_ymls(tmp_path):
    """Works for non-Dockerfile patterns too."""
    _init_git(tmp_path)
    (tmp_path / ".agent-harness.yml").write_text("stacks: [python]")
    sub = tmp_path / "backend"
    sub.mkdir()
    (sub / ".agent-harness.yml").write_text("stacks: [docker]")
    result = find_files(tmp_path, ["**/.agent-harness.yml", ".agent-harness.yml"])
    assert len(result) == 2
