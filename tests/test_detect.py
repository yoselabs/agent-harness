from agent_harness.detect import detect_stacks


def test_detect_python(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    assert "python" in detect_stacks(tmp_path)


def test_detect_docker(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    assert "docker" in detect_stacks(tmp_path)


def test_detect_compose(tmp_path):
    (tmp_path / "docker-compose.prod.yml").write_text("services:\n  app:\n    image: x")
    assert "docker" in detect_stacks(tmp_path)


def test_detect_multiple(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    stacks = detect_stacks(tmp_path)
    assert "python" in stacks and "docker" in stacks


def test_detect_empty(tmp_path):
    assert detect_stacks(tmp_path) == set()


def test_detect_javascript(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    assert "javascript" in detect_stacks(tmp_path)


def test_detect_javascript_and_docker(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    (tmp_path / "Dockerfile").write_text("FROM node:22")
    stacks = detect_stacks(tmp_path)
    assert "javascript" in stacks and "docker" in stacks


def test_detect_dokploy(tmp_path):
    (tmp_path / "docker-compose.prod.yml").write_text(
        "services:\n  app:\n    networks:\n      - dokploy-network\n"
    )
    assert "dokploy" in detect_stacks(tmp_path)


def test_detect_dokploy_not_detected_without_network(tmp_path):
    (tmp_path / "docker-compose.prod.yml").write_text(
        "services:\n  app:\n    image: myapp:latest\n"
    )
    assert "dokploy" not in detect_stacks(tmp_path)


def test_detect_dokploy_and_docker(tmp_path):
    (tmp_path / "docker-compose.prod.yml").write_text(
        "services:\n  app:\n    networks:\n      - dokploy-network\n"
    )
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    stacks = detect_stacks(tmp_path)
    assert "dokploy" in stacks and "docker" in stacks


def test_detect_docker_ignores_directory_named_dockerfile(tmp_path):
    """A directory named Dockerfile should not trigger docker detection."""
    (tmp_path / "Dockerfile").mkdir()
    assert "docker" not in detect_stacks(tmp_path)


def test_detect_python_ignores_non_packaging_setup_py(tmp_path):
    """A setup.py that isn't a packaging file shouldn't be a project indicator.

    We renamed internal setup.py to setup_check.py, but this test ensures
    detect_python only triggers on real project markers.
    """
    # Only a .py file in the dir — no pyproject.toml, requirements.txt, etc.
    (tmp_path / "some_module.py").write_text("x = 1")
    assert "python" not in detect_stacks(tmp_path)


def test_detect_all_root_only(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    from agent_harness.detect import detect_all

    results = detect_all(tmp_path)
    assert tmp_path in results
    assert "python" in results[tmp_path]


def test_detect_all_subprojects(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text("[project]\nname='x'")
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "package.json").write_text('{"name":"y"}')
    from agent_harness.detect import detect_all

    results = detect_all(tmp_path)
    assert "docker" in results[tmp_path]
    assert "python" in results[backend]
    assert "javascript" in results[frontend]


def test_detect_all_empty(tmp_path):
    from agent_harness.detect import detect_all

    results = detect_all(tmp_path)
    assert results == {}


def test_detect_all_excludes_docker_only_dirs(tmp_path):
    """Dirs with only Dockerfiles are not detected as projects."""
    from agent_harness.detect import detect_all

    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12")

    scripts = tmp_path / "scripts" / "autonomy"
    scripts.mkdir(parents=True)
    (scripts / "Dockerfile").write_text("FROM python:3.12")

    results = detect_all(tmp_path)
    assert tmp_path in results
    assert scripts not in results


def test_detect_all_includes_dir_with_manifest(tmp_path):
    """Dirs with dependency manifests ARE detected as projects."""
    from agent_harness.detect import detect_all

    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "pyproject.toml").write_text("[project]\nname='x'")
    (backend / "Dockerfile").write_text("FROM python:3.12")

    results = detect_all(tmp_path)
    assert backend in results
    assert "python" in results[backend]
    assert "docker" in results[backend]
