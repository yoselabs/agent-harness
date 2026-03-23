# Full Restructure: Declarative Presets

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite agent-harness from "tool wrappers organized by stack" to "declarative presets with a consistent interface." Each preset is self-contained. The runner is generic. Policies are overridable. `init` shows diffs against best practices.

**Key principle:** The Rego policies are the product. Everything else is plumbing.

---

## Target Structure

```
agent_harness/
  __init__.py              # version, POLICIES_DIR
  cli.py                   # Click: detect, init, lint, fix (thin — each is one loop)

  # Core — shared infrastructure, doesn't change when adding presets
  config.py                # load .agent-harness.yml, merge preset configs
  runner.py                # run_check(), CheckResult, tool_available()
  conftest.py              # run_conftest() — shared, replaces 6 copies
  exclusions.py            # file exclusion patterns
  workspace.py             # discover subproject roots

  # Preset system
  preset.py                # Preset base class + ToolInfo/PresetInfo dataclasses
  registry.py              # PRESETS list + UNIVERSAL — explicit imports

  # Presets — each is self-contained, implements Preset interface
  presets/
    __init__.py
    universal/
      __init__.py          # UniversalPreset(Preset)
      yamllint_check.py
      gitignore_check.py
      json_check.py
      file_length_check.py
      templates.py

    python/
      __init__.py          # PythonPreset(Preset)
      config.py            # PythonConfig dataclass
      detect.py            # detect_python()
      ruff_check.py
      ty_check.py
      conftest_check.py    # pyproject.toml policies
      fix.py               # ruff --fix, ruff format
      templates.py

    javascript/
      __init__.py          # JavaScriptPreset(Preset)
      config.py            # JavaScriptConfig
      detect.py
      biome_check.py
      type_check.py
      conftest_check.py    # package.json policies
      fix.py               # biome check --fix
      templates.py

    docker/
      __init__.py          # DockerPreset(Preset)
      config.py            # DockerConfig
      detect.py
      hadolint_check.py
      conftest_dockerfile.py
      conftest_compose.py
      templates.py

    dokploy/
      __init__.py          # DokployPreset(Preset)
      detect.py
      conftest_check.py

  # Policies — Rego (bundled, the real product)
  policies/
    python/
    javascript/
    dockerfile/
    compose/
    dokploy/
    gitignore/

  # Scaffolding
  init/
    scaffold.py            # reads preset.get_info(), generates config
    templates.py           # shared templates (Makefile, .agent-harness.yml)

# Plugin (Claude Code)
skills/
  agent-harness/
    SKILL.md
    docker-guidance.md
    python-guidance.md
```

## The Preset Interface

```python
# preset.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from agent_harness.runner import CheckResult


@dataclass
class ToolInfo:
    name: str              # display name
    description: str       # what it does
    binary: str            # for tool_available() check
    install_hint: str      # how to install


@dataclass
class PresetInfo:
    name: str
    tools: list[ToolInfo]


class Preset:
    """Base class for all presets. Each preset must implement these methods."""

    name: str = ""

    def detect(self, project_dir: Path) -> bool:
        """Return True if this preset applies to the project."""
        return False

    def run_checks(self, project_dir: Path, config: dict, exclude: list[str]) -> list[CheckResult]:
        """Run all checks for this preset. Return results."""
        return []

    def run_fix(self, project_dir: Path, config: dict) -> list[str]:
        """Auto-fix what's fixable. Return list of actions taken."""
        return []

    def get_info(self) -> PresetInfo:
        """Return metadata for init display."""
        return PresetInfo(name=self.name, tools=[])

    def get_config_defaults(self) -> dict:
        """Return default config values for this preset."""
        return {}
```

## The Registry

```python
# registry.py
from agent_harness.presets.python import PythonPreset
from agent_harness.presets.javascript import JavaScriptPreset
from agent_harness.presets.docker import DockerPreset
from agent_harness.presets.dokploy import DokployPreset
from agent_harness.presets.universal import UniversalPreset

PRESETS = [PythonPreset(), JavaScriptPreset(), DockerPreset(), DokployPreset()]
UNIVERSAL = UniversalPreset()
```

## The Orchestrators (each is ~10 lines)

```python
# lint.py
from agent_harness.config import load_config
from agent_harness.exclusions import get_excluded_patterns
from agent_harness.registry import PRESETS, UNIVERSAL
from agent_harness.workspace import discover_roots
from agent_harness.runner import CheckResult


def run_lint(project_dir: Path) -> list[CheckResult]:
    config = load_config(project_dir)
    exclude = get_excluded_patterns(config.get("exclude", []))
    results = UNIVERSAL.run_checks(project_dir, config, exclude)
    for preset in PRESETS:
        if preset.name in config.get("stacks", set()):
            results.extend(preset.run_checks(project_dir, config, exclude))
    return results


def run_lint_all(project_dir: Path) -> dict[Path, list[CheckResult]]:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    roots = discover_roots(project_dir)
    if not roots:
        return {project_dir: run_lint(project_dir)}
    results = {}
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(run_lint, root): root for root in roots}
        for future in as_completed(futures):
            root = futures[future]
            try:
                results[root] = future.result()
            except Exception as e:
                results[root] = [CheckResult(name="error", passed=False, error=str(e))]
    return results
```

## Shared Conftest Runner

```python
# conftest.py
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path
from agent_harness import POLICIES_DIR
from agent_harness.runner import CheckResult, run_check


def run_conftest(
    name: str,
    project_dir: Path,
    target_file: str,
    policy_subdir: str,
    data: dict | None = None,
) -> CheckResult:
    """Run conftest on a target file with policies from a subdirectory."""
    target = project_dir / target_file
    if not target.exists():
        return CheckResult(name=name, passed=True, output=f"Skipping {name}: {target_file} not found")

    policy_path = POLICIES_DIR / policy_subdir
    cmd = ["conftest", "test", str(target), "--policy", str(policy_path), "--no-color", "--all-namespaces"]

    data_path = None
    if data:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, tmp)
        tmp.close()
        data_path = tmp.name
        cmd.extend(["--data", data_path])

    try:
        return run_check(name, cmd, cwd=str(project_dir))
    finally:
        if data_path:
            os.unlink(data_path)
```

## Config Changes

`config.py` becomes simpler — it loads YAML and returns a dict. Each preset reads its own section:

```python
# config.py
from pathlib import Path
import yaml
from agent_harness.registry import PRESETS

def load_config(project_dir: Path) -> dict:
    """Load .agent-harness.yml. Returns dict with stacks, exclude, per-preset config."""
    cfg_path = project_dir / ".agent-harness.yml"
    config = {"stacks": set(), "exclude": []}

    if cfg_path.exists():
        try:
            raw = yaml.safe_load(cfg_path.read_text()) or {}
        except yaml.YAMLError as e:
            import click
            click.echo(f"  WARNING: {cfg_path} is malformed, using defaults\n  {e}", err=True)
            raw = {}

        if "stacks" in raw:
            config["stacks"] = set(raw["stacks"])
        if "exclude" in raw:
            config["exclude"] = list(raw["exclude"])

        # Per-preset config sections
        for preset in PRESETS:
            if preset.name in raw:
                config[preset.name] = raw[preset.name]

    # Auto-detect if no stacks specified
    if not config["stacks"]:
        from agent_harness.registry import PRESETS
        config["stacks"] = {p.name for p in PRESETS if p.detect(project_dir)}

    return config
```

## Example Preset: Python

```python
# presets/python/__init__.py
from pathlib import Path
from agent_harness.preset import Preset, PresetInfo, ToolInfo
from agent_harness.runner import CheckResult


class PythonPreset(Preset):
    name = "python"

    def detect(self, project_dir: Path) -> bool:
        from .detect import detect_python
        return detect_python(project_dir)

    def run_checks(self, project_dir: Path, config: dict, exclude: list[str]) -> list[CheckResult]:
        from .ruff_check import run_ruff
        from .ty_check import run_ty
        from .conftest_check import run_conftest_python
        results = []
        results.extend(run_ruff(project_dir))
        results.append(run_ty(project_dir))
        results.append(run_conftest_python(project_dir))
        return results

    def run_fix(self, project_dir: Path, config: dict) -> list[str]:
        from .fix import run_python_fix
        return run_python_fix(project_dir)

    def get_info(self) -> PresetInfo:
        return PresetInfo(name="python", tools=[
            ToolInfo("ruff", "linting + formatting", "ruff", "uv add ruff --dev"),
            ToolInfo("ty", "type checking", "ty", "uv add ty --dev"),
            ToolInfo("conftest", "pyproject.toml enforcement", "conftest", "brew install conftest"),
        ])
```

## What Changes From Today

| Today | After |
|-------|-------|
| `stacks/` | `presets/` |
| `_run_conftest` in 6 files | `conftest.py` shared module |
| HarnessConfig dataclass with hardcoded stack configs | Dict-based config, each preset owns its section |
| fix.py has all fix logic | Each preset has its own `fix.py` |
| detect.py imports all stack detectors | Registry loop: `preset.detect()` |
| lint.py imports all checks explicitly | Registry loop: `preset.run_checks()` |
| STACK_DESCRIPTIONS in scaffold.py | `preset.get_info()` |
| own_image_prefix silently ignored | Passed via `conftest.py` shared runner's `data` param |
| yamllint temp file leak | Fixed in shared conftest.py pattern |
| No YAML error handling | try/except in config.py |

## Tasks

### Task 1: Core infrastructure
Create `preset.py`, `conftest.py`, `registry.py`. Update `config.py` (dict-based, YAML error handling), `runner.py` (add `tool_available` if not there).

### Task 2: Move stacks/ → presets/, implement Preset interface
Rename directory. Each preset gets `__init__.py` with class. Move fix logic from root fix.py into per-preset fix.py. Individual check files stay but use shared `conftest.py`.

### Task 3: Thin orchestrators
Rewrite `lint.py`, `fix.py`, `detect.py` as registry loops. ~10 lines each.

### Task 4: Update CLI + init
cli.py delegates to thin orchestrators. init/scaffold.py uses `preset.get_info()`.

### Task 5: Fix deferred issues
- own_image_prefix via conftest.py data param
- yamllint temp file cleanup
- file_length uses config overrides

### Task 6: Tests
Update all imports. Verify 89+ tests pass. Add preset interface tests.

### Task 7: Integration test + docs
Run on agent-harness, blog, proxy-hub. Update README, CLAUDE.md, CONTRIBUTING.md.
