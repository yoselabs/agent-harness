import json
from unittest.mock import patch, MagicMock
from agent_harness.presets.javascript.type_check import run_type_check, detect_framework


def test_detect_astro(tmp_path):
    pkg = {"dependencies": {"astro": "^6.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    assert detect_framework(tmp_path) == "astro"


def test_detect_next(tmp_path):
    pkg = {"dependencies": {"next": "^15.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    assert detect_framework(tmp_path) == "next"


def test_detect_default(tmp_path):
    pkg = {"dependencies": {"express": "^4.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    assert detect_framework(tmp_path) is None


def test_astro_uses_astro_check(tmp_path):
    pkg = {"dependencies": {"astro": "^6.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    with patch(
        "agent_harness.presets.javascript.type_check.shutil.which",
        return_value="/usr/bin/astro",
    ):
        with patch("agent_harness.presets.javascript.type_check.run_check") as mock_run:
            mock_run.return_value = MagicMock(passed=True)
            run_type_check(tmp_path)
            cmd = mock_run.call_args[0][1]
            assert "astro" in cmd and "check" in cmd


def test_detect_wasp(tmp_path):
    (tmp_path / ".wasproot").write_text("File marking the root of Wasp project.")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))
    assert detect_framework(tmp_path) == "wasp"


def test_wasp_runs_compile_then_tsc(tmp_path):
    (tmp_path / ".wasproot").write_text("File marking the root of Wasp project.")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))

    def which_side_effect(tool):
        return f"/usr/bin/{tool}" if tool in ("wasp", "tsc") else None

    with patch(
        "agent_harness.presets.javascript.type_check.shutil.which",
        side_effect=which_side_effect,
    ):
        with patch("agent_harness.presets.javascript.type_check.run_check") as mock_run:
            mock_run.return_value = MagicMock(passed=True)
            run_type_check(tmp_path)
            # Should call wasp compile first, then tsc
            assert mock_run.call_count == 2
            first_call = mock_run.call_args_list[0]
            assert first_call[0][0] == "typecheck:wasp-compile"
            assert first_call[0][1] == ["wasp", "compile"]
            second_call = mock_run.call_args_list[1]
            assert second_call[0][0] == "typecheck:wasp"
            assert "tsc" in second_call[0][1]


def test_wasp_compile_failure_stops_before_tsc(tmp_path):
    (tmp_path / ".wasproot").write_text("File marking the root of Wasp project.")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))

    with patch(
        "agent_harness.presets.javascript.type_check.shutil.which",
        return_value="/usr/bin/wasp",
    ):
        with patch("agent_harness.presets.javascript.type_check.run_check") as mock_run:
            mock_run.return_value = MagicMock(
                passed=False, name="typecheck:wasp-compile"
            )
            result = run_type_check(tmp_path)
            # Should only call wasp compile, not tsc
            assert mock_run.call_count == 1
            assert not result.passed


def test_wasp_missing_cli(tmp_path):
    (tmp_path / ".wasproot").write_text("File marking the root of Wasp project.")
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {}}))
    with patch(
        "agent_harness.presets.javascript.type_check.shutil.which",
        return_value=None,
    ):
        result = run_type_check(tmp_path)
        assert not result.passed
        assert "not found" in result.output.lower()


def test_fallback_uses_tsc(tmp_path):
    pkg = {"dependencies": {"express": "^4.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    with patch(
        "agent_harness.presets.javascript.type_check.shutil.which",
        return_value="/usr/bin/tsc",
    ):
        with patch("agent_harness.presets.javascript.type_check.run_check") as mock_run:
            mock_run.return_value = MagicMock(passed=True)
            run_type_check(tmp_path)
            cmd = mock_run.call_args[0][1]
            assert "tsc" in cmd
