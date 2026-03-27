from agent_harness.presets.universal.yamllint_check import run_yamllint


def test_yamllint_no_yaml_files(tmp_path):
    """Skip gracefully when no YAML files are tracked."""
    result = run_yamllint(tmp_path)
    assert result.passed


def test_yamllint_skips_lock_files(tmp_path, monkeypatch):
    """Lock files should be excluded even if git-tracked."""
    import subprocess

    def mock_run(cmd, **kwargs):
        if "ls-files" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="pnpm-lock.yaml\n", stderr=""
            )
        return subprocess.run(cmd, **kwargs)

    monkeypatch.setattr(
        "agent_harness.presets.universal.yamllint_check.subprocess.run", mock_run
    )
    # Create file on disk so .exists() filter doesn't swallow it
    (tmp_path / "pnpm-lock.yaml").write_text("key: value\n")
    result = run_yamllint(tmp_path, exclude_patterns=["*-lock.*", "*.lock"])
    assert result.passed
    assert "skipping" in result.output.lower() or "No YAML" in result.output


def test_yamllint_skips_deleted_files(tmp_path, monkeypatch):
    """Files returned by git ls-files but deleted from disk should be skipped."""
    import subprocess

    _real_run = subprocess.run

    def mock_run(cmd, **kwargs):
        if "ls-files" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout="deleted.yaml\nexists.yaml\n", stderr=""
            )
        return _real_run(cmd, **kwargs)

    monkeypatch.setattr(
        "agent_harness.presets.universal.yamllint_check.subprocess.run", mock_run
    )
    # Only create exists.yaml — deleted.yaml is "tracked" but not on disk
    (tmp_path / "exists.yaml").write_text("key: value\n")
    result = run_yamllint(tmp_path)
    # Should not crash; exists.yaml should be processed (pass or fail depending on yamllint availability)
    assert "deleted.yaml" not in result.output
