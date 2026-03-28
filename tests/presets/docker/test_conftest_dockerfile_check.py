from pathlib import Path

from agent_harness.presets.docker.conftest_dockerfile_check import (
    run_conftest_dockerfile,
)

_GOOD_DOCKERFILE = (
    "FROM python:3.12-bookworm-slim\nWORKDIR /app\n"
    "COPY pyproject.toml uv.lock ./\n"
    "RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev\n"
    "COPY src/ ./src/\nUSER nonroot\n"
    "HEALTHCHECK CMD curl -f http://localhost/ || exit 1\n"
)

_BAD_NO_USER = (
    "FROM python:3.12-bookworm-slim\nWORKDIR /app\nCOPY . .\n"
    "RUN uv sync\nHEALTHCHECK CMD curl -f http://localhost/ || exit 1\n"
)


def test_conftest_dockerfile_good(tmp_path):
    (tmp_path / "Dockerfile").write_text(_GOOD_DOCKERFILE)
    results = run_conftest_dockerfile(tmp_path)
    assert all(r.passed for r in results), (
        f"Expected pass but got: {[r.error for r in results]}"
    )


def test_conftest_dockerfile_bad_no_user(tmp_path):
    (tmp_path / "Dockerfile").write_text(_BAD_NO_USER)
    results = run_conftest_dockerfile(tmp_path)
    assert any(not r.passed for r in results)


def test_conftest_no_dockerfile(tmp_path):
    results = run_conftest_dockerfile(tmp_path)
    assert all(r.passed for r in results)


def test_conftest_multi_dockerfile(tmp_path):
    """Checks multiple Dockerfiles when given a list."""
    (tmp_path / "Dockerfile").write_text(_GOOD_DOCKERFILE)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "Dockerfile").write_text(_BAD_NO_USER)

    results = run_conftest_dockerfile(
        tmp_path,
        dockerfiles=[Path("Dockerfile"), Path("scripts/Dockerfile")],
    )
    assert len(results) == 2
    root_result = [r for r in results if r.name == "conftest-dockerfile"][0]
    assert root_result.passed
    sub_result = [r for r in results if "scripts" in r.name][0]
    assert not sub_result.passed


def test_conftest_skip_exception(tmp_path):
    """conftest_skip suppresses specific policy violations."""
    (tmp_path / "Dockerfile").write_text(_BAD_NO_USER)
    results = run_conftest_dockerfile(
        tmp_path,
        dockerfiles=[Path("Dockerfile")],
        conftest_skip={
            "Dockerfile": ["dockerfile.user", "dockerfile.layers", "dockerfile.cache"]
        },
    )
    assert all(r.passed for r in results)


def test_conftest_skip_per_file(tmp_path):
    """Different skip lists per Dockerfile path."""
    (tmp_path / "Dockerfile").write_text(_GOOD_DOCKERFILE)
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "Dockerfile").write_text(_BAD_NO_USER)

    results = run_conftest_dockerfile(
        tmp_path,
        dockerfiles=[Path("Dockerfile"), Path("scripts/Dockerfile")],
        conftest_skip={
            "scripts/Dockerfile": [
                "dockerfile.user",
                "dockerfile.layers",
                "dockerfile.cache",
            ],
        },
    )
    assert all(r.passed for r in results)
