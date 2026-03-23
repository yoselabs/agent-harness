from agent_harness.stacks.dokploy.conftest_dokploy_check import run_conftest_dokploy


def test_conftest_dokploy_no_file(tmp_path):
    """Skip gracefully when no compose file exists."""
    result = run_conftest_dokploy(tmp_path)
    assert result.passed
