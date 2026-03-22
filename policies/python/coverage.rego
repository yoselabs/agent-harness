package python.coverage

# COVERAGE CONFIG — show gaps, not green files
#
# WHAT: Ensures coverage output is optimized so agents see gaps, not noise.
#
# WHY (skip_covered): With 95% coverage, most files are green. Without
# skip_covered, the agent sees 50+ fully-covered files drowning the 2 that
# actually need work. Signal-to-noise ratio collapses.
# WHY (branch): Line-only coverage misses untested if/else branches. Code
# can have 100% line coverage but skip entire conditional paths.
#
# WITHOUT IT: Agent wastes time scrolling through green files looking for
# the one uncovered module. Untested branches silently pass coverage gates.
#
# FIX: Set skip_covered = true in [tool.coverage.report] and branch = true
# in [tool.coverage.run].
#
# Input: parsed pyproject.toml (TOML -> JSON)

import rego.v1

# ── Policy: skip_covered = true ──
# Without this, agent sees 50+ fully-covered files drowning 2 that need work.

deny contains msg if {
	report := input.tool.coverage.report
	not report.skip_covered
	msg := "coverage.report: missing 'skip_covered' — set to true so agents only see files with gaps"
}

deny contains msg if {
	report := input.tool.coverage.report
	report.skip_covered == false
	msg := "coverage.report: skip_covered is false — set to true so agents only see files with gaps"
}

# ── Policy: branch coverage enabled ──
# Line-only coverage misses untested if/else branches.

deny contains msg if {
	run := input.tool.coverage.run
	not run.branch
	msg := "coverage.run: missing 'branch' — set to true to catch untested if/else branches"
}

deny contains msg if {
	run := input.tool.coverage.run
	run.branch == false
	msg := "coverage.run: branch is false — set to true to catch untested if/else branches"
}

# ── Policy: show_missing = false ──
# Missing line numbers in terminal add noise; XML report has them for diff-cover.

warn contains msg if {
	report := input.tool.coverage.report
	report.show_missing == true
	msg := "coverage.report: show_missing is true — consider false to reduce noise (XML report has line numbers for diff-cover)"
}
