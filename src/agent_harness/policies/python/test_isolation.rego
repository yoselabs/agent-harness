package python.test_isolation

# TEST ISOLATION — pytest-env prevents production DB hits
#
# WHAT: Ensures pytest-env is configured to inject test environment variables
# before pydantic-settings reads them.
#
# WHY: Without pytest-env, agents run tests against whatever DATABASE_URL is
# in the shell. On a dev machine, that might be the production database.
# Separate test DB port (5433 vs 5432) prevents accidental writes to prod.
#
# WITHOUT IT: Agent runs `make test`, tests execute against production
# database. Data gets corrupted or deleted with no warning.
#
# FIX: Add pytest-env to dev dependencies and configure env entries in
# [tool.pytest.ini_options] with test-specific values (e.g., DATABASE_URL
# pointing to localhost:5433/test_db).
#
# Input: parsed pyproject.toml (TOML -> JSON)

import rego.v1

# ── Policy: pytest-env configured ──
# Without this, agents run tests against whatever DATABASE_URL is in the shell.
# pytest-env injects test values BEFORE pydantic-settings reads them.

deny contains msg if {
	opts := input.tool.pytest.ini_options
	not opts.env
	msg := "pytest: no 'env' configuration — add pytest-env entries to isolate tests from production (e.g., test database URL on a separate port)"
}
