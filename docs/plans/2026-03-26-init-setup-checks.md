# Init Setup Checks — Python-based diagnostic + fix

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace init's conftest-based diagnostic with Python setup checks that can both diagnose AND fix configuration issues. Rego stays lint-only. Clean separation of concerns.

**Architecture:** Each preset gets a `setup.py` with check functions that return `SetupIssue` objects. Each issue has a severity (critical/recommendation), a message, and an optional `fix` callable. Init runs these checks, displays results, and applies fixes. Rego policies stay in `policies/` for lint enforcement only — `warn` rules move to Python setup checks.

**Tech Stack:** Python 3.12+, tomlkit (TOML read/write preserving formatting), click (CLI)

---

## Policy Design Strategy

This is the governing principle for where any check belongs. Reference this when adding new checks.

### The boundary: "Is it broken?"

```
"Would any reasonable person agree this is broken?"
  YES → lint (Rego deny rule, every commit)
  NO, it's debatable → init (Python setup check, on-demand)
```

### Lint (Rego, every commit)
- **Purpose:** Enforce that gates EXIST. Binary pass/fail.
- **Rules:** Only `deny`. No `warn` (warn rules move to init Python).
- **Examples:**
  - `--strict-markers` missing from addopts → deny (broken: marker typos silently pass)
  - `--cov-fail-under` missing from addopts → deny (broken: no coverage gate at all)
  - `--cov-fail-under` < 30% → deny (broken: a 25% gate catches nothing meaningful)
  - `.env` not in .gitignore → deny (broken: secrets will leak)

### Init (Python, on-demand with fixes)
- **Purpose:** Diagnose configuration QUALITY. Fix what's fixable. Warn about the rest.
- **Severities:**
  - `critical` — objectively misconfigured, has auto-fix (e.g., `--cov-fail-under` missing → add with 95%)
  - `recommendation` — debatable, inform only (e.g., threshold is 70% → suggest 90-95%)
- **Examples:**
  - `--cov-fail-under` missing → critical + fix: add `--cov-fail-under=95`
  - `--cov-fail-under=50` → recommendation: "consider 90-95%"
  - `-v` missing from addopts → critical + fix: add it
  - `ruff output-format` is "full" → recommendation: "consider concise"

### Same topic, different concerns

A single topic (like coverage threshold) can have BOTH a lint rule and an init check:
- **Lint Rego:** "Does `--cov-fail-under` exist? Is it >= 30%?" — gate presence + sanity floor
- **Init Python:** "Is the value optimal? Should we set it higher?" — quality + fix

They're complementary: lint catches regressions every commit, init sets things up right.

---

## Target UX

```
$ agent-harness init

  Detected: python

  python:
    ✗ pyproject.toml: --cov-fail-under not set                   critical (fixable)
    ✗ pyproject.toml: addopts missing -v                          critical (fixable)
    ~ pyproject.toml: --cov-fail-under=50, recommend 90-95%       recommendation
    ✓ ruff installed
    ✓ ty installed
    ✓ conftest installed

  universal:
    ✓ yamllint installed
    ✓ conftest installed

  Files to create:
    + .agent-harness.yml
    + .yamllint.yml

  2 critical (2 fixable), 1 recommendation, 2 files to create.

  To apply fixes and create files:
    agent-harness init --apply
```

```
$ agent-harness init --apply

  Detected: python

  python:
    ✓ fixed: added --cov-fail-under=95 to addopts
    ✓ fixed: added -v to addopts
    ~ pyproject.toml: --cov-fail-under=50, recommend 90-95%       recommendation
    ✓ ruff installed
    ✓ ty installed
    ✓ conftest installed

  Created:
    + .agent-harness.yml
    + .yamllint.yml

  1 recommendation remains.
```

---

## File Structure

### New
```
src/agent_harness/
  setup.py                        # SetupIssue dataclass, SetupResult, base types
  presets/
    python/setup.py               # Python setup checks with fixes
    javascript/setup.py           # JS setup checks with fixes (future — stub for now)
    docker/setup.py               # Docker setup checks with fixes (future — stub)
    universal/setup.py            # Universal setup checks with fixes (future — stub)
```

### Modify
```
src/agent_harness/
  cli.py                          # Wire --apply flag, update --help text
  preset.py                       # Add run_setup() to Preset interface
  init/
    scaffold.py                   # Use setup checks instead of conftest diagnostic
    diagnostic.py                 # Adapt display to SetupIssue (replaces DiagnosticResult)
  conftest.py                     # Remove run_conftest_diagnostic, DiagnosticResult
  policies/python/pytest.rego     # Add deny for threshold < 30%, remove warn for -v
  policies/python/pytest_test.rego
  policies/python/coverage.rego   # Remove warn for show_missing (moves to init)
  policies/python/coverage_test.rego
  pyproject.toml                  # Add tomlkit dependency
```

### Delete
```
tests/test_conftest_diagnostic.py  # Tests for removed run_conftest_diagnostic
```

### Unchanged
```
  conftest.py (run_conftest stays) # Lint still uses this
  runner.py
  lint.py, fix.py, detect.py
  All individual check files (*_check.py)
  All Rego deny rules
```

---

## Tasks

### Task 0: Add tomlkit dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add tomlkit to dependencies**

In `pyproject.toml`, add `tomlkit` to the dependencies list:

```toml
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "tomlkit>=0.13",
]
```

- [ ] **Step 2: Install**

Run: `uv sync`

- [ ] **Step 3: Verify import works**

Run: `uv run python -c "import tomlkit; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "deps: add tomlkit for TOML read/write in init setup checks"
```

---

### Task 1: SetupIssue dataclass and framework

Create the core types that all setup checks use.

**Files:**
- Create: `src/agent_harness/setup.py`
- Create: `tests/test_setup.py`

- [ ] **Step 1: Write tests for SetupIssue**

Create `tests/test_setup.py`:

```python
"""Tests for setup check framework."""

from __future__ import annotations

from agent_harness.setup import SetupIssue


def test_setup_issue_critical_with_fix():
    fix_called = []
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under not set",
        severity="critical",
        fix=lambda project_dir: fix_called.append(True),
    )
    assert issue.severity == "critical"
    assert issue.fixable
    assert issue.fix is not None
    from pathlib import Path
    issue.fix(Path("/tmp"))
    assert fix_called == [True]


def test_setup_issue_recommendation_no_fix():
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under=50, recommend 90-95%",
        severity="recommendation",
    )
    assert issue.severity == "recommendation"
    assert not issue.fixable


def test_setup_issue_fixable_property():
    fixable = SetupIssue(
        file="x", message="m", severity="critical", fix=lambda p: None
    )
    not_fixable = SetupIssue(file="x", message="m", severity="critical")
    assert fixable.fixable is True
    assert not_fixable.fixable is False
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/test_setup.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Create src/agent_harness/setup.py**

```python
"""Setup check framework — diagnose + fix for init command."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class SetupIssue:
    """A single issue found by a setup check."""

    file: str
    message: str
    severity: str  # "critical" | "recommendation"
    fix: Callable[[Path], None] | None = None

    @property
    def fixable(self) -> bool:
        return self.fix is not None
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/test_setup.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_harness/setup.py tests/test_setup.py
git commit -m "feat: SetupIssue dataclass for init setup checks"
```

---

### Task 2: Python preset setup checks with fixes

The first real setup.py — checks pyproject.toml for pytest/coverage config and can fix issues.

**Files:**
- Create: `src/agent_harness/presets/python/setup.py`
- Create: `tests/presets/python/test_setup.py`

- [ ] **Step 1: Write tests**

Create `tests/presets/python/test_setup.py`:

```python
"""Tests for Python preset setup checks."""

from __future__ import annotations

from pathlib import Path

from agent_harness.presets.python.setup import check_python_setup


def _write_pyproject(tmp_path: Path, content: str) -> Path:
    """Write a pyproject.toml and return the project dir."""
    (tmp_path / "pyproject.toml").write_text(content)
    return tmp_path


def test_missing_cov_fail_under(tmp_path):
    """Missing --cov-fail-under → critical + fixable."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov"
""")
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    assert len(cov_issues) == 1
    assert cov_issues[0].severity == "critical"
    assert cov_issues[0].fixable


def test_missing_cov_fail_under_fix_applies(tmp_path):
    """Fix adds --cov-fail-under=95 to addopts."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov"
""")
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    cov_issues[0].fix(tmp_path)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "--cov-fail-under=95" in content
    # Original flags preserved
    assert "--strict-markers" in content
    assert "--cov" in content


def test_low_threshold_recommendation(tmp_path):
    """Threshold 50% → recommendation (not critical, above 30%)."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=50"
""")
    issues = check_python_setup(tmp_path)
    cov_issues = [i for i in issues if "cov-fail-under" in i.message]
    assert len(cov_issues) == 1
    assert cov_issues[0].severity == "recommendation"
    assert not cov_issues[0].fixable  # Don't auto-change user's chosen value


def test_missing_verbose_flag(tmp_path):
    """Missing -v → critical + fixable."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "--strict-markers --cov --cov-fail-under=95"
""")
    issues = check_python_setup(tmp_path)
    v_issues = [i for i in issues if "-v" in i.message]
    assert len(v_issues) == 1
    assert v_issues[0].severity == "critical"
    assert v_issues[0].fixable


def test_missing_verbose_fix_applies(tmp_path):
    """Fix adds -v to addopts."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "--strict-markers --cov --cov-fail-under=95"
""")
    issues = check_python_setup(tmp_path)
    v_issues = [i for i in issues if "-v" in i.message]
    v_issues[0].fix(tmp_path)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "-v" in content


def test_good_config_no_issues(tmp_path):
    """Well-configured project → no issues."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = true

[tool.coverage.run]
branch = true
""")
    issues = check_python_setup(tmp_path)
    assert issues == []


def test_no_pyproject_no_issues(tmp_path):
    """No pyproject.toml → empty list (nothing to check)."""
    issues = check_python_setup(tmp_path)
    assert issues == []


def test_missing_skip_covered(tmp_path):
    """Missing skip_covered → critical + fixable."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = false

[tool.coverage.run]
branch = true
""")
    issues = check_python_setup(tmp_path)
    skip_issues = [i for i in issues if "skip_covered" in i.message]
    assert len(skip_issues) == 1
    assert skip_issues[0].severity == "critical"
    assert skip_issues[0].fixable


def test_missing_branch_coverage(tmp_path):
    """Missing branch coverage → critical + fixable."""
    _write_pyproject(tmp_path, """\
[tool.pytest.ini_options]
addopts = "-v --strict-markers --cov --cov-fail-under=95"

[tool.coverage.report]
skip_covered = true
""")
    issues = check_python_setup(tmp_path)
    branch_issues = [i for i in issues if "branch" in i.message]
    assert len(branch_issues) == 1
    assert branch_issues[0].severity == "critical"
    assert branch_issues[0].fixable
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `uv run pytest tests/presets/python/test_setup.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement check_python_setup**

Create `src/agent_harness/presets/python/setup.py`:

```python
"""Python preset setup checks — diagnose + fix pyproject.toml configuration."""

from __future__ import annotations

import re
from pathlib import Path

import tomlkit

from agent_harness.setup import SetupIssue


def check_python_setup(project_dir: Path) -> list[SetupIssue]:
    """Check pyproject.toml for pytest/coverage configuration issues."""
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    doc = tomlkit.parse(pyproject_path.read_text())
    issues: list[SetupIssue] = []

    issues.extend(_check_pytest_addopts(doc))
    issues.extend(_check_coverage_report(doc))
    issues.extend(_check_coverage_run(doc))

    return issues


def _get_addopts(doc: tomlkit.TOMLDocument) -> str | None:
    """Extract addopts string from [tool.pytest.ini_options]."""
    try:
        return doc["tool"]["pytest"]["ini_options"]["addopts"]
    except (KeyError, TypeError):
        return None


def _patch_addopts(project_dir: Path, flag: str) -> None:
    """Append a flag to addopts in pyproject.toml, preserving formatting."""
    pyproject_path = project_dir / "pyproject.toml"
    doc = tomlkit.parse(pyproject_path.read_text())
    current = doc["tool"]["pytest"]["ini_options"]["addopts"]
    doc["tool"]["pytest"]["ini_options"]["addopts"] = current + " " + flag
    pyproject_path.write_text(tomlkit.dumps(doc))


def _check_pytest_addopts(doc: tomlkit.TOMLDocument) -> list[SetupIssue]:
    """Check pytest addopts for required flags."""
    addopts = _get_addopts(doc)
    if addopts is None:
        return []  # No pytest config — nothing to check

    issues: list[SetupIssue] = []

    # -v flag
    if "-v" not in addopts:
        issues.append(SetupIssue(
            file="pyproject.toml",
            message="addopts missing '-v' — agents need individual test names",
            severity="critical",
            fix=lambda p: _patch_addopts(p, "-v"),
        ))

    # --cov-fail-under
    if "--cov-fail-under" not in addopts:
        issues.append(SetupIssue(
            file="pyproject.toml",
            message="--cov-fail-under not set — adding with 95%",
            severity="critical",
            fix=lambda p: _patch_addopts(p, "--cov-fail-under=95"),
        ))
    else:
        # Extract threshold value
        match = re.search(r"--cov-fail-under=(\d+)", addopts)
        if match:
            threshold = int(match.group(1))
            if 30 <= threshold < 90:
                issues.append(SetupIssue(
                    file="pyproject.toml",
                    message=f"--cov-fail-under={threshold}%, recommend 90-95%",
                    severity="recommendation",
                ))

    return issues


def _check_coverage_report(doc: tomlkit.TOMLDocument) -> list[SetupIssue]:
    """Check [tool.coverage.report] settings."""
    try:
        report = doc["tool"]["coverage"]["report"]
    except (KeyError, TypeError):
        return []

    issues: list[SetupIssue] = []

    skip_covered = report.get("skip_covered")
    if skip_covered is not True:
        def fix_skip_covered(project_dir: Path) -> None:
            pyproject_path = project_dir / "pyproject.toml"
            d = tomlkit.parse(pyproject_path.read_text())
            d["tool"]["coverage"]["report"]["skip_covered"] = True
            pyproject_path.write_text(tomlkit.dumps(d))

        issues.append(SetupIssue(
            file="pyproject.toml",
            message="coverage.report: skip_covered not true — agents see noise from covered files",
            severity="critical",
            fix=fix_skip_covered,
        ))

    return issues


def _check_coverage_run(doc: tomlkit.TOMLDocument) -> list[SetupIssue]:
    """Check [tool.coverage.run] settings."""
    try:
        run = doc["tool"]["coverage"]["run"]
    except (KeyError, TypeError):
        return []

    issues: list[SetupIssue] = []

    branch = run.get("branch")
    if branch is not True:
        def fix_branch(project_dir: Path) -> None:
            pyproject_path = project_dir / "pyproject.toml"
            d = tomlkit.parse(pyproject_path.read_text())
            d["tool"]["coverage"]["run"]["branch"] = True
            pyproject_path.write_text(tomlkit.dumps(d))

        issues.append(SetupIssue(
            file="pyproject.toml",
            message="coverage.run: branch not true — line-only coverage misses untested branches",
            severity="critical",
            fix=fix_branch,
        ))

    return issues
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `uv run pytest tests/presets/python/test_setup.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add src/agent_harness/presets/python/setup.py tests/presets/python/test_setup.py
git commit -m "feat: Python setup checks with fix capability for init"
```

---

### Task 3: Rego policy cleanup — remove warn rules, add threshold floor

Lint Rego should only have `deny` rules. Move `warn` rules to Python setup checks (done in Task 2 for Python). Add a `deny` floor for absurdly low thresholds (< 30%).

**Files:**
- Modify: `src/agent_harness/policies/python/pytest.rego`
- Modify: `src/agent_harness/policies/python/pytest_test.rego`
- Modify: `src/agent_harness/policies/python/coverage.rego`
- Modify: `src/agent_harness/policies/python/coverage_test.rego`

Note: JavaScript `warn` rules (`package.rego` lines 38-47) stay for now — no JS setup.py yet. They'll move when JS setup checks are built. They're harmless in lint (conftest ignores warnings).

- [ ] **Step 1: Remove warn from pytest.rego**

In `src/agent_harness/policies/python/pytest.rego`, remove the `-v` warn rule (lines 36-44) and add a deny for threshold < 30%.

The file should become:

```rego
package python.pytest

# PYTEST CONFIG — strict markers, integrated coverage
#
# WHAT: Ensures pytest is configured with strict markers and coverage.
# These are gates that must exist. Value judgments (thresholds, verbosity)
# are handled by init setup checks, not lint.
#
# LINT RULES (deny): Gate exists? Is it objectively broken?
# INIT CHECKS (Python): Is it optimally configured? Fix it.
#
# Input: parsed pyproject.toml (TOML -> JSON)

import rego.v1

# ── deny: strict-markers must be enabled ──

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--strict-markers")
	msg := "pytest: addopts missing '--strict-markers' — catches marker typos deterministically"
}

# ── deny: coverage must be enabled ──

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--cov")
	msg := "pytest: addopts missing '--cov' — coverage should run with every test invocation"
}

# ── deny: coverage threshold must exist ──

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	not contains(addopts, "--cov-fail-under")
	msg := "pytest: addopts missing '--cov-fail-under' — set a coverage threshold (recommended: 95)"
}

# ── deny: coverage threshold must not be absurdly low ──
# Below 30% is not a gate — it catches nothing meaningful.

deny contains msg if {
	opts := input.tool.pytest.ini_options
	addopts := opts.addopts
	contains(addopts, "--cov-fail-under")
	parts := split(addopts, "--cov-fail-under=")
	count(parts) > 1
	threshold_str := split(parts[1], " ")[0]
	threshold := to_number(threshold_str)
	threshold < 30
	msg := sprintf("pytest: --cov-fail-under=%v is below 30%% — this gate catches nothing meaningful", [threshold])
}
```

- [ ] **Step 2: Update pytest_test.rego**

```rego
package python.pytest_test

import rego.v1

import data.python.pytest

# ── DENY: missing strict-markers ──

test_missing_strict_markers_fires if {
	pytest.deny with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --cov --cov-fail-under=95"}}}}
}

# ── DENY: missing --cov ──

test_missing_cov_fires if {
	pytest.deny with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --strict-markers --cov-fail-under=95"}}}}
}

# ── DENY: missing --cov-fail-under ──

test_missing_cov_fail_under_fires if {
	pytest.deny with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --strict-markers --cov"}}}}
}

# ── DENY: absurdly low threshold ──

test_threshold_below_30_fires if {
	pytest.deny with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --strict-markers --cov --cov-fail-under=15"}}}}
}

# ── PASS: threshold at 30 is acceptable ──

test_threshold_at_30_passes if {
	count(pytest.deny) == 0 with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --strict-markers --cov --cov-fail-under=30"}}}}
}

# ── PASS: good config ──

test_good_config_passes if {
	count(pytest.deny) == 0 with input as {"tool": {"pytest": {"ini_options": {"addopts": "-v --strict-markers --cov --cov-fail-under=95"}}}}
}
```

- [ ] **Step 3: Remove warn from coverage.rego**

In `src/agent_harness/policies/python/coverage.rego`, remove the `show_missing` warn rule (lines 53-60). Update the file header to reflect lint-only deny rules. The rest stays.

Remove this block:
```rego
# ── Policy: show_missing = false ──
# Missing line numbers in terminal add noise; XML report has them for diff-cover.

warn contains msg if {
	report := input.tool.coverage.report
	report.show_missing == true
	msg := "coverage.report: show_missing is true — consider false to reduce noise (XML report has line numbers for diff-cover)"
}
```

- [ ] **Step 4: Update coverage_test.rego if it tests the removed warn**

Check if `coverage_test.rego` has tests for the removed `show_missing` warn. If so, remove those tests.

- [ ] **Step 5: Verify all Rego tests pass**

Run: `conftest verify --policy src/agent_harness/policies/python/`
Expected: all tests pass, 0 failures

- [ ] **Step 6: Verify lint still passes**

Run: `make lint`
Expected: all checks pass

- [ ] **Step 7: Commit**

```bash
git add src/agent_harness/policies/python/
git commit -m "refactor: Rego policies deny-only — warn rules move to Python setup checks"
```

---

### Task 4: Wire Preset.run_setup() and update display layer

Add `run_setup()` to the Preset interface. Update display to use `SetupIssue` instead of `DiagnosticResult`. Remove `run_conftest_diagnostic` and `DiagnosticResult` from conftest.py.

**Files:**
- Modify: `src/agent_harness/preset.py`
- Modify: `src/agent_harness/presets/python/__init__.py`
- Modify: `src/agent_harness/presets/docker/__init__.py`
- Modify: `src/agent_harness/presets/javascript/__init__.py`
- Modify: `src/agent_harness/presets/dokploy/__init__.py`
- Modify: `src/agent_harness/presets/universal/__init__.py`
- Modify: `src/agent_harness/init/diagnostic.py`
- Modify: `src/agent_harness/conftest.py`
- Modify: `tests/test_diagnostic.py`
- Delete: `tests/test_conftest_diagnostic.py`

- [ ] **Step 1: Add run_setup() to Preset base class**

In `src/agent_harness/preset.py`, add import and method:

```python
from agent_harness.setup import SetupIssue

class Preset:
    ...
    def run_setup(self, project_dir: Path, config: dict) -> list[SetupIssue]:
        """Run setup checks. Returns issues with optional fixes."""
        return []
```

Remove the `DiagnosticResult` import and `run_diagnostic()` method.

- [ ] **Step 2: Implement run_setup() in PythonPreset**

In `src/agent_harness/presets/python/__init__.py`:

```python
def run_setup(self, project_dir, config):
    from .setup import check_python_setup
    return check_python_setup(project_dir)
```

Remove `run_diagnostic()`.

- [ ] **Step 3: Remove run_diagnostic() from all other presets, add stub run_setup()**

In docker, javascript, dokploy, universal `__init__.py` files:
- Remove `run_diagnostic()` method
- Each keeps the default `run_setup()` from base class (returns `[]`) until their setup.py is built

- [ ] **Step 4: Update diagnostic.py to use SetupIssue**

Rewrite `src/agent_harness/init/diagnostic.py`:

```python
"""Diagnostic display for init command."""

from __future__ import annotations

from pathlib import Path

import click

from agent_harness.preset import ToolInfo
from agent_harness.runner import tool_available
from agent_harness.setup import SetupIssue


def display_setup_issues(
    preset_name: str,
    issues: list[SetupIssue],
    tools: list[ToolInfo],
    project_dir: Path,
) -> tuple[int, int, int]:
    """Display setup check results. Returns (critical_count, recommendation_count, fixable_count)."""
    click.echo(f"\n  {preset_name}:")

    critical_count = 0
    recommendation_count = 0
    fixable_count = 0

    for issue in issues:
        if issue.severity == "critical":
            suffix = " (fixable)" if issue.fixable else ""
            click.echo(f"    ✗ {issue.file}: {issue.message}    critical{suffix}")
            critical_count += 1
            if issue.fixable:
                fixable_count += 1
        else:
            click.echo(f"    ~ {issue.file}: {issue.message}    recommendation")
            recommendation_count += 1

    for tool in tools:
        available = tool_available(tool.binary, project_dir)
        if available:
            click.echo(f"    ✓ {tool.name} installed")
        else:
            click.echo(f"    ✗ {tool.name} not installed    ({tool.install_hint})")
            critical_count += 1

    return critical_count, recommendation_count, fixable_count


def display_summary(
    critical: int, recommendations: int, fixable: int, missing_files: int
) -> None:
    """Display final summary line."""
    parts = []
    if critical:
        fix_note = f" ({fixable} fixable)" if fixable else ""
        parts.append(f"{critical} critical{fix_note}")
    if recommendations:
        parts.append(f"{recommendations} recommendation{'s' if recommendations != 1 else ''}")
    if missing_files:
        parts.append(f"{missing_files} file{'s' if missing_files != 1 else ''} to create")

    if parts:
        click.echo(f"\n  {', '.join(parts)}.")
    else:
        click.echo("\n  All checks passed.")
```

- [ ] **Step 5: Remove run_conftest_diagnostic and DiagnosticResult from conftest.py**

In `src/agent_harness/conftest.py`:
- Remove the `DiagnosticResult` dataclass
- Remove the `run_conftest_diagnostic()` function
- Remove the `subprocess` import (only needed by diagnostic)
- Remove `_resolve_tool` from the import (only needed by diagnostic)
- Keep `run_conftest()` — lint still uses it

The file should just have the original `run_conftest()` function.

- [ ] **Step 6: Delete tests/test_conftest_diagnostic.py**

```bash
rm tests/test_conftest_diagnostic.py
```

- [ ] **Step 7: Update tests/test_diagnostic.py**

Rewrite to test `display_setup_issues` and updated `display_summary`:

```python
"""Tests for diagnostic display module."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import patch

from agent_harness.init.diagnostic import display_setup_issues, display_summary
from agent_harness.preset import ToolInfo
from agent_harness.setup import SetupIssue


def capture_output(fn, *args, **kwargs):
    output = StringIO()
    with patch(
        "click.echo", side_effect=lambda x="", **kw: output.write(str(x) + "\n")
    ):
        result = fn(*args, **kwargs)
    return output.getvalue(), result


def test_display_critical_fixable():
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under not set",
        severity="critical",
        fix=lambda p: None,
    )
    text, (c, r, f) = capture_output(
        display_setup_issues, "python", [issue], [], Path("/tmp")
    )
    assert "✗" in text
    assert "critical" in text
    assert "fixable" in text
    assert c == 1 and r == 0 and f == 1


def test_display_critical_not_fixable():
    issue = SetupIssue(
        file="pyproject.toml",
        message="something wrong",
        severity="critical",
    )
    text, (c, r, f) = capture_output(
        display_setup_issues, "python", [issue], [], Path("/tmp")
    )
    assert "✗" in text
    assert "critical" in text
    assert "fixable" not in text
    assert c == 1 and f == 0


def test_display_recommendation():
    issue = SetupIssue(
        file="pyproject.toml",
        message="--cov-fail-under=50, recommend 90-95%",
        severity="recommendation",
    )
    text, (c, r, f) = capture_output(
        display_setup_issues, "python", [issue], [], Path("/tmp")
    )
    assert "~" in text
    assert "recommendation" in text
    assert c == 0 and r == 1


def test_display_tools_available():
    tool = ToolInfo(name="ruff", description="linter", binary="ruff", install_hint="pip install ruff")
    with patch("agent_harness.init.diagnostic.tool_available", return_value=True):
        text, (c, r, f) = capture_output(
            display_setup_issues, "python", [], [tool], Path("/tmp")
        )
    assert "✓" in text
    assert "ruff installed" in text


def test_display_tools_missing():
    tool = ToolInfo(name="ruff", description="linter", binary="ruff", install_hint="pip install ruff")
    with patch("agent_harness.init.diagnostic.tool_available", return_value=False):
        text, (c, r, f) = capture_output(
            display_setup_issues, "python", [], [tool], Path("/tmp")
        )
    assert "✗" in text
    assert "ruff not installed" in text
    assert c == 1


def test_display_summary_with_fixable():
    text, _ = capture_output(display_summary, 3, 1, 2, 1)
    assert "3 critical (2 fixable)" in text
    assert "1 recommendation" in text
    assert "1 file to create" in text


def test_display_summary_all_passed():
    text, _ = capture_output(display_summary, 0, 0, 0, 0)
    assert "All checks passed" in text
```

- [ ] **Step 8: Run all tests**

Run: `uv run pytest tests/ -v --tb=short`
Expected: all pass (count will decrease by ~5 from removed diagnostic tests, increase from new ones)

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: replace conftest diagnostic with SetupIssue-based display"
```

---

### Task 5: Rewrite scaffold.py and CLI for --apply flow

Wire setup checks + scaffolding into the new init flow. Add `--apply` flag.

**Files:**
- Modify: `src/agent_harness/init/scaffold.py`
- Modify: `src/agent_harness/cli.py`
- Modify: `tests/test_init.py`

- [ ] **Step 1: Rewrite scaffold.py**

```python
"""Init command — diagnose project setup, scaffold configs, apply fixes."""

from __future__ import annotations

from pathlib import Path

import click

from agent_harness.config import load_config
from agent_harness.detect import detect_stacks
from agent_harness.init.diagnostic import display_setup_issues, display_summary
from agent_harness.init.templates import (
    HARNESS_YML,
    MAKEFILE,
    PRECOMMIT_YML,
    YAMLLINT_YML,
)
from agent_harness.presets.javascript.templates import BIOME_CONFIG
from agent_harness.registry import PRESETS, UNIVERSAL
from agent_harness.setup import SetupIssue


def scaffold_project(project_dir: Path, apply: bool = False) -> list[str]:
    """Diagnose setup, optionally apply fixes and scaffold files."""
    stacks = detect_stacks(project_dir)
    stacks_str = ", ".join(sorted(stacks)) if stacks else "none detected"
    stacks_list = ", ".join(sorted(stacks))

    config = load_config(project_dir)

    click.echo(f"  Detected: {stacks_str}")

    total_critical = 0
    total_recommendations = 0
    total_fixable = 0
    all_issues: list[SetupIssue] = []

    # Run setup checks for each active preset
    for preset in PRESETS:
        if preset.name in stacks:
            issues = preset.run_setup(project_dir, config)
            info = preset.get_info()
            c, r, f = display_setup_issues(
                preset.name, issues, info.tools, project_dir
            )
            total_critical += c
            total_recommendations += r
            total_fixable += f
            all_issues.extend(issues)

    # Run universal setup checks
    universal_issues = UNIVERSAL.run_setup(project_dir, config)
    universal_info = UNIVERSAL.get_info()
    c, r, f = display_setup_issues(
        "universal", universal_issues, universal_info.tools, project_dir
    )
    total_critical += c
    total_recommendations += r
    total_fixable += f
    all_issues.extend(universal_issues)

    # Determine files to scaffold
    if "python" in stacks:
        test_command = "uv run pytest tests/ -v"
    elif "javascript" in stacks:
        test_command = "npm test"
    else:
        test_command = 'echo "no test command configured"'

    files: dict[str, str] = {
        ".agent-harness.yml": HARNESS_YML.format(
            stacks=stacks_str, stacks_list=stacks_list
        ),
        ".yamllint.yml": YAMLLINT_YML,
        ".pre-commit-config.yaml": PRECOMMIT_YML,
        "Makefile": MAKEFILE.format(test_command=test_command),
    }

    if "javascript" in stacks:
        files["biome.json"] = BIOME_CONFIG

    missing_files = [f for f in files if not (project_dir / f).exists()]

    if missing_files:
        click.echo("\n  Files to create:")
        for filename in missing_files:
            click.echo(f"    + {filename}")

    display_summary(
        total_critical, total_recommendations, total_fixable, len(missing_files)
    )

    if not apply:
        # Report mode — show what would be done
        if total_fixable or missing_files:
            click.echo(
                "\n  To apply fixes and create files:\n"
                "    agent-harness init --apply"
            )
        return []

    # Apply mode — fix issues and scaffold files
    actions: list[str] = []

    # Apply fixes
    fixable_issues = [i for i in all_issues if i.fixable]
    for issue in fixable_issues:
        issue.fix(project_dir)
        actions.append(f"FIXED  {issue.file}: {issue.message}")

    # Scaffold files
    for filename, content in files.items():
        path = project_dir / filename
        if path.exists():
            actions.append(f"SKIP  {filename} (already exists)")
        else:
            path.write_text(content)
            actions.append(f"CREATE  {filename}")

    return actions
```

- [ ] **Step 2: Update CLI**

In `src/agent_harness/cli.py`, update the init command:

```python
@cli.command()
@click.option("--apply", is_flag=True, help="Apply fixes and create missing files")
def init(apply):
    """Diagnose harness setup: check tools, config quality, missing files.

    Without --apply: report mode (shows issues, suggests fixes).
    With --apply: applies auto-fixes and creates missing config files.

    Setup checks diagnose configuration quality (thresholds, flags,
    coverage settings) and offer fixes. Lint checks run separately
    via 'agent-harness lint' for fast pass/fail enforcement.

    Examples:
      agent-harness init            # diagnose only
      agent-harness init --apply    # diagnose and fix
    """
    from agent_harness.init.scaffold import scaffold_project

    actions = scaffold_project(Path.cwd(), apply=apply)
    for action in actions:
        click.echo(f"  {action}")
    if actions and actions[0] != "Cancelled":
        click.echo("\n  Done. Run: make lint")
```

- [ ] **Step 3: Update tests/test_init.py**

The existing tests use `yes=True` parameter which changes to `apply=True`:

```python
# tests/test_init.py
from agent_harness.init.scaffold import scaffold_project


def test_scaffold_creates_files(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=True)
    assert (tmp_path / ".agent-harness.yml").exists()
    assert (tmp_path / ".yamllint.yml").exists()
    assert (tmp_path / ".pre-commit-config.yaml").exists()
    assert any("CREATE" in a for a in actions)


def test_scaffold_skips_existing(tmp_path):
    (tmp_path / ".agent-harness.yml").write_text("stacks: [python]")
    actions = scaffold_project(tmp_path, apply=True)
    assert any("SKIP" in a and ".agent-harness.yml" in a for a in actions)
    assert (tmp_path / ".agent-harness.yml").read_text() == "stacks: [python]"


def test_scaffold_creates_makefile(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    scaffold_project(tmp_path, apply=True)
    assert (tmp_path / "Makefile").exists()
    content = (tmp_path / "Makefile").read_text()
    assert "agent-harness lint" in content
    assert "pytest" in content


def test_scaffold_makefile_js_test_command(tmp_path):
    (tmp_path / "package.json").write_text('{"name":"x"}')
    scaffold_project(tmp_path, apply=True)
    content = (tmp_path / "Makefile").read_text()
    assert "npm test" in content


def test_scaffold_skips_existing_makefile(tmp_path):
    (tmp_path / "Makefile").write_text("custom: echo hi")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=True)
    assert "SKIP  Makefile" in " ".join(actions)
    assert (tmp_path / "Makefile").read_text() == "custom: echo hi"


def test_report_mode_returns_empty(tmp_path):
    """Without apply, returns empty list (report only)."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'")
    actions = scaffold_project(tmp_path, apply=False)
    assert actions == []
    assert not (tmp_path / ".agent-harness.yml").exists()


def test_apply_fixes_pyproject(tmp_path):
    """With apply, fixes are applied to pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("""\
[project]
name = "x"

[tool.pytest.ini_options]
addopts = "--strict-markers --cov"
""")
    actions = scaffold_project(tmp_path, apply=True)
    content = (tmp_path / "pyproject.toml").read_text()
    assert "--cov-fail-under=95" in content
    assert "-v" in content
    assert any("FIXED" in a for a in actions)
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/ -v --tb=short`
Expected: all pass

- [ ] **Step 5: Run make lint**

Run: `make lint`
Expected: all pass

- [ ] **Step 6: Test the UX manually**

Run: `agent-harness init` (report mode, no --apply)
Run: `agent-harness init --help` (verify help text is complete)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat: init --apply flow with Python setup checks and auto-fixes"
```

---

### Task 6: Document policy design strategy in CLAUDE.md

Add the policy design strategy to the project's CLAUDE.md so future agents know where to put new checks.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add policy strategy section**

Add after the "Conventions" section:

```markdown
## Policy Design Strategy

Every check belongs in exactly one place. The boundary:

**"Would any reasonable person agree this is broken?"**
- YES → lint (Rego `deny` rule in `policies/`)
- Debatable → init (Python setup check in `presets/*/setup.py`)

### Lint (Rego, every commit)
- Only `deny` rules. No `warn`.
- Checks that gates EXIST and aren't objectively broken.
- Examples: `--strict-markers` missing, `--cov-fail-under` missing, threshold < 30%

### Init (Python, on-demand)
- `SetupIssue` with severity `critical` (fixable) or `recommendation`.
- Checks configuration QUALITY. Can auto-fix.
- Examples: threshold = 50% (recommend 90-95%), missing `-v` flag

### Same topic, both places
A single topic (e.g., coverage threshold) can have both:
- Lint Rego: "does the gate exist? Is it >= 30%?" (broken gate detection)
- Init Python: "is the value optimal? fix to 95%" (quality + auto-fix)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: policy design strategy — lint vs init placement rules"
```

---

### Task 7: Final cleanup and integration verification

Remove all dead code, run full test suite, lint, Rego tests.

**Files:**
- Verify: all files touched in previous tasks
- Clean: any remaining references to `DiagnosticResult` or `run_conftest_diagnostic`

- [ ] **Step 1: Search for dead references**

```bash
grep -r "DiagnosticResult" src/ tests/
grep -r "run_conftest_diagnostic" src/ tests/
grep -r "run_diagnostic" src/ tests/
```

Remove any remaining references.

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: all pass

- [ ] **Step 3: Run Rego tests**

Run: `conftest verify --policy src/agent_harness/policies/`
Expected: all pass

- [ ] **Step 4: Run lint**

Run: `make lint`
Expected: all pass

- [ ] **Step 5: Test init on self**

Run: `agent-harness init`
Run: `agent-harness init --apply`
Run: `agent-harness init --help`

Verify UX matches target.

- [ ] **Step 6: Commit any cleanup**

```bash
git add -A
git commit -m "chore: final cleanup — remove dead diagnostic code, verify all checks pass"
```
