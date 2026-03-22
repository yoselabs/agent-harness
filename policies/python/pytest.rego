package python.pytest

# PYTEST CONFIG — strict markers, verbose output, integrated coverage
#
# WHAT: Ensures pytest is configured with strict markers, verbose output,
# and coverage running on every test invocation.
#
# WHY (strict-markers): Without it, marker typos silently pass. Agents create
# @pytest.mark.untit instead of @pytest.mark.unit and the test silently
# doesn't run in filtered mode. No error, no warning.
# WHY (verbose): Agent needs individual test names to identify failures.
# Without -v, output shows dots and the agent can't tell which test failed.
# WHY (cov): Coverage should run with every test invocation, not as a separate
# step. Agents forget to run coverage separately, so gaps go undetected.
#
# WITHOUT IT: Phantom test markers that select nothing, opaque dot-based
# output, and coverage gaps discovered only in CI.
#
# FIX: Set addopts = "-v --strict-markers --cov --cov-fail-under=95" in
# [tool.pytest.ini_options].
#
# Input: parsed pyproject.toml (TOML -> JSON)

import rego.v1

# ── Policy: strict-markers enabled ──
# Without strict-markers, marker typos silently pass — agents create wrong markers.

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--strict-markers")
	msg := "pytest: addopts missing '--strict-markers' — catches marker typos deterministically"
}

# ── Policy: verbose output ──
# Agent needs individual test names to identify failures.

warn contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "-v")
	msg := "pytest: addopts missing '-v' — agents need individual test names to identify failures"
}

# ── Policy: coverage enabled in addopts ──

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--cov")
	msg := "pytest: addopts missing '--cov' — coverage should run with every test invocation"
}

# ── Policy: coverage fail-under threshold ──

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--cov-fail-under")
	msg := "pytest: addopts missing '--cov-fail-under' — set a coverage threshold (recommended: 95)"
}
