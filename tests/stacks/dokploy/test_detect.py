from agent_harness.stacks.dokploy.detect import detect_dokploy


def test_detect_dokploy_from_prod_compose(tmp_path):
    """Detect dokploy when docker-compose.prod.yml references dokploy-network."""
    (tmp_path / "docker-compose.prod.yml").write_text(
        "services:\n  app:\n    networks:\n      - dokploy-network\n"
    )
    assert detect_dokploy(tmp_path) is True


def test_detect_dokploy_from_compose(tmp_path):
    """Detect dokploy when docker-compose.yml references dokploy-network."""
    (tmp_path / "docker-compose.yml").write_text(
        "networks:\n  dokploy-network:\n    external: true\n"
    )
    assert detect_dokploy(tmp_path) is True


def test_no_dokploy_without_network(tmp_path):
    """No detection when compose exists but no dokploy-network."""
    (tmp_path / "docker-compose.prod.yml").write_text(
        "services:\n  app:\n    image: myapp:latest\n"
    )
    assert detect_dokploy(tmp_path) is False


def test_no_dokploy_no_compose(tmp_path):
    """No detection when no compose files exist."""
    assert detect_dokploy(tmp_path) is False


def test_prod_compose_takes_priority(tmp_path):
    """Detect from docker-compose.prod.yml even if docker-compose.yml has no dokploy-network."""
    (tmp_path / "docker-compose.prod.yml").write_text(
        "networks:\n  dokploy-network:\n    external: true\n"
    )
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  app:\n    image: myapp:latest\n"
    )
    assert detect_dokploy(tmp_path) is True
