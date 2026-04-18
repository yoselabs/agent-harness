# agent-weiss Foundations (MVP) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a working agent-weiss skeleton with one end-to-end control proving the entire pattern (state file + reconciliation + bundle resolution + check.sh contract + fixture testing + skill.md driver).

**Architecture:** Python helper library (`agent_weiss.lib`) provides hashing, state I/O, bundle resolution, reconciliation, and `check.sh` dispatch. `skill.md` is the Claude Code agent-facing markdown that orchestrates the user loop by invoking helper modules. Per-control artifacts (`prescribed.yaml`, `check.sh`, `policy.rego`, `instruct.md`) live in the `profiles/` tree.

**Tech Stack:**
- Python 3.12+ (helpers, tests)
- `uv` (package management)
- `pytest` (test runner including fixtures)
- `ruamel.yaml` (round-trip YAML preserving comments/order)
- `conftest` 0.56+ (Rego policy execution)
- `gitleaks` (used by one control for fixtures only — install required for tests)
- Claude Code skill format (`skill.md` + supporting files)
- POSIX shell for `check.sh` files

**Repository:** Will create `yoselabs/agent-weiss` (does not yet exist). Local clone path: `/Users/iorlas/Workspaces/agent-weiss`.

**Spec / roadmap:**
- `docs/superpowers/specs/2026-04-14-agent-weiss-design.md`
- `docs/superpowers/plans/2026-04-14-agent-weiss-roadmap.md` (cross-cutting decisions live here — DO NOT restate in this plan)

**Plan scope (in):** repo skeleton, schemas, state I/O, bundle resolution, reconciliation, contract parser, ONE end-to-end control, fixture infra, basic skill.md.

**Plan scope (out):** approval UX polish (Plan 3), full control library (Plan 2), distribution packaging (Plan 5), drift refresh UX (Plan 6).

---

## Task 0: Create the agent-weiss repository

**Files:**
- Create: `/Users/iorlas/Workspaces/agent-weiss/` (new directory + git repo)

- [ ] **Step 1: Create new GitHub repo under yoselabs org**

Run:
```bash
gh repo create yoselabs/agent-weiss --public --description "Skill-first agent-readiness audit and setup for any codebase"
```

Expected: prompts for confirmation (`--confirm` is deprecated in newer `gh`); answer yes if prompted. Returns the repo URL.

- [ ] **Step 2: Clone locally**

Run:
```bash
cd /Users/iorlas/Workspaces && gh repo clone yoselabs/agent-weiss
```

Expected: `Cloning into 'agent-weiss'...` followed by warning about empty repo.

- [ ] **Step 3: Initial commit with README**

Create `/Users/iorlas/Workspaces/agent-weiss/README.md`:
```markdown
# agent-weiss

A Claude Code skill that audits and sets up codebases to be agent-ready.

Named after Grimoire Weiss from NieR — the white sentient grimoire that accompanies the protagonist.

**Status:** Pre-alpha (under active development).

**Spec:** See `docs/spec.md` (copied from yoselabs/agent-harness during initial development).
```

Run:
```bash
cd /Users/iorlas/Workspaces/agent-weiss
git add README.md
git commit -m "chore: initial commit"
git branch -M main
git push -u origin main
```

Expected: First commit pushed to origin.

- [ ] **Step 4: Copy the spec from agent-harness for reference**

Run:
```bash
mkdir -p /Users/iorlas/Workspaces/agent-weiss/docs
cp /Users/iorlas/Workspaces/agent-harness/docs/superpowers/specs/2026-04-14-agent-weiss-design.md /Users/iorlas/Workspaces/agent-weiss/docs/spec.md
```

- [ ] **Step 5: Commit the spec**

Run:
```bash
cd /Users/iorlas/Workspaces/agent-weiss
git add docs/spec.md
git commit -m "docs: copy approved design spec from agent-harness"
git push
```

---

## Task 1: Python project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/agent_weiss/__init__.py`
- Create: `src/agent_weiss/lib/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`
- Create: `.python-version`

- [ ] **Step 1: Create `.python-version`**

```
3.12
```

- [ ] **Step 2: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.agent-weiss/
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[project]
name = "agent-weiss"
version = "0.0.1"
description = "Skill-first agent-readiness audit and setup for any codebase"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12"
authors = [{name = "Denis Tomilin"}]

dependencies = [
    "ruamel.yaml>=0.18",
]

[project.urls]
Homepage = "https://github.com/yoselabs/agent-weiss"
Repository = "https://github.com/yoselabs/agent-weiss"
Issues = "https://github.com/yoselabs/agent-weiss/issues"

# Note: no [project.scripts] section in Plan 1. Helper modules are invoked
# by skill.md via `python -m agent_weiss.lib.<module>`; CLI entry points
# (if needed) come in Plan 5 (Distribution Packaging).

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/agent_weiss"]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "ruff>=0.7",
    "ty>=0.0.1a3",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers"
```

- [ ] **Step 4: Create empty package files**

```bash
mkdir -p src/agent_weiss/lib tests
touch src/agent_weiss/__init__.py src/agent_weiss/lib/__init__.py tests/__init__.py
```

- [ ] **Step 5: Verify uv sync**

Run:
```bash
cd /Users/iorlas/Workspaces/agent-weiss
uv sync
```

Expected: `Resolved N packages in...` followed by install lines. No errors.

- [ ] **Step 6: Commit**

```bash
git add .python-version .gitignore pyproject.toml uv.lock src/ tests/
git commit -m "chore: python project scaffolding"
git push
```

---

## Task 2: Lock `prescribed.yaml` schema

**Files:**
- Create: `src/agent_weiss/lib/schemas.py`
- Create: `tests/test_schemas_prescribed.py`

This task locks the per-control prescribed configuration schema. Every control in the bundle ships one of these.

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemas_prescribed.py`:

```python
"""Tests for prescribed.yaml schema validation."""
import pytest
from agent_weiss.lib.schemas import validate_prescribed, PrescribedSchema


def test_prescribed_minimal_valid():
    """A minimal prescribed.yaml has id, version, what, why, applies_to."""
    data = {
        "id": "universal.docs.agents-md-present",
        "version": 1,
        "what": "Project has an AGENTS.md file at the repository root.",
        "why": "AGENTS.md is the cross-tool standard for instructing AI coding agents.",
        "applies_to": ["any"],
    }
    result = validate_prescribed(data)
    assert isinstance(result, PrescribedSchema)
    assert result.id == "universal.docs.agents-md-present"


def test_prescribed_with_install_per_os():
    """prescribed.yaml may declare install commands per OS."""
    data = {
        "id": "universal.security.gitleaks-configured",
        "version": 1,
        "what": "gitleaks pre-commit hook is installed and configured.",
        "why": "Detects committed secrets before they leave the developer machine.",
        "applies_to": ["any"],
        "install": {
            "macos": "brew install gitleaks",
            "linux": "apt install gitleaks || nix-shell -p gitleaks",
        },
    }
    result = validate_prescribed(data)
    assert result.install["macos"] == "brew install gitleaks"


def test_prescribed_missing_required_field_raises():
    """Missing a required field raises ValueError with the field name."""
    data = {"id": "x", "version": 1, "what": "x", "why": "x"}  # missing applies_to
    with pytest.raises(ValueError, match="applies_to"):
        validate_prescribed(data)


def test_prescribed_id_format():
    """id must be dot-delimited: profile.domain.control-name."""
    data = {
        "id": "invalid_no_dots",
        "version": 1,
        "what": "x",
        "why": "x",
        "applies_to": ["any"],
    }
    with pytest.raises(ValueError, match="id format"):
        validate_prescribed(data)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_schemas_prescribed.py -v
```

Expected: All 4 tests FAIL with import error or undefined-name error on `validate_prescribed` / `PrescribedSchema`.

- [ ] **Step 3: Write minimal implementation**

Create `src/agent_weiss/lib/schemas.py`:

```python
"""Schema validation for prescribed.yaml and bundle.yaml.

Schemas are simple dataclasses validated by hand. This avoids a heavy
schema library dependency and keeps the surface readable for contributors.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any

ID_PATTERN = re.compile(r"^[a-z0-9-]+\.[a-z0-9-]+\.[a-z0-9-]+$")


@dataclass(frozen=True)
class PrescribedSchema:
    """A single control's prescribed configuration.

    Required fields: id, version, what, why, applies_to.
    Optional: install (per-OS shell command), config_fragment, depends_on.
    """
    id: str
    version: int
    what: str
    why: str
    applies_to: list[str]
    install: dict[str, str] = field(default_factory=dict)
    config_fragment: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


# applies_to vocabulary (v1):
# - "any" — applies to any project regardless of stack
# - "<profile_id>" — applies when this profile matches (e.g., "python", "typescript", "docker")
# - The list is OR-ed: `["python", "typescript"]` means applies if either profile matches.
# Validation does NOT enforce vocabulary in v1 (free-form strings); profile matchers in
# Plan 3+4 will define which strings are recognized. Keep entries lowercase, hyphenated.


_REQUIRED_FIELDS = ("id", "version", "what", "why", "applies_to")


def validate_prescribed(data: dict[str, Any]) -> PrescribedSchema:
    """Validate a prescribed.yaml dict and return a PrescribedSchema.

    Raises ValueError on missing required fields or invalid id format.
    """
    for field_name in _REQUIRED_FIELDS:
        if field_name not in data:
            raise ValueError(f"prescribed.yaml missing required field: {field_name}")

    if not ID_PATTERN.match(data["id"]):
        raise ValueError(
            f"id format invalid: {data['id']!r}. Expected: profile.domain.control-name"
        )

    return PrescribedSchema(
        id=data["id"],
        version=int(data["version"]),
        what=data["what"],
        why=data["why"],
        applies_to=list(data["applies_to"]),
        install=dict(data.get("install", {})),
        config_fragment=dict(data.get("config_fragment", {})),
        depends_on=list(data.get("depends_on", [])),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_schemas_prescribed.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/schemas.py tests/test_schemas_prescribed.py
git commit -m "feat: prescribed.yaml schema with validation"
git push
```

---

## Task 3: Lock `bundle.yaml` schema

**Files:**
- Modify: `src/agent_weiss/lib/schemas.py`
- Create: `tests/test_schemas_bundle.py`

`bundle.yaml` is the bundle manifest at the bundle root. It has the bundle version + a per-file SHA index used for drift detection.

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemas_bundle.py`:

```python
"""Tests for bundle.yaml schema validation."""
import pytest
from agent_weiss.lib.schemas import validate_bundle, BundleSchema


def test_bundle_minimal_valid():
    """A minimal bundle.yaml has version, files."""
    data = {
        "version": "0.0.1",
        "files": {
            "profiles/universal/domains/docs/controls/agents-md-present/policy.rego": "abc123",
            "profiles/universal/domains/docs/controls/agents-md-present/check.sh": "def456",
        },
    }
    result = validate_bundle(data)
    assert isinstance(result, BundleSchema)
    assert result.version == "0.0.1"
    assert len(result.files) == 2


def test_bundle_lookup_file_hash():
    """BundleSchema.hash_for(path) returns the recorded sha256 or None."""
    data = {
        "version": "0.0.1",
        "files": {"a/b/c.rego": "abc123"},
    }
    bundle = validate_bundle(data)
    assert bundle.hash_for("a/b/c.rego") == "abc123"
    assert bundle.hash_for("missing/file.rego") is None


def test_bundle_missing_version_raises():
    """Missing version field raises ValueError."""
    data = {"files": {}}
    with pytest.raises(ValueError, match="version"):
        validate_bundle(data)


def test_bundle_files_must_be_mapping():
    """files must be a dict (path → sha256), not a list."""
    data = {"version": "0.0.1", "files": ["a/b.rego"]}
    with pytest.raises(ValueError, match="files"):
        validate_bundle(data)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_schemas_bundle.py -v
```

Expected: All 4 tests FAIL with `validate_bundle` undefined.

- [ ] **Step 3: Add implementation to `schemas.py`**

Append to `src/agent_weiss/lib/schemas.py`:

```python


@dataclass(frozen=True)
class BundleSchema:
    """The bundle's manifest, located at <bundle_root>/bundle.yaml.

    files: mapping of bundle-relative path → sha256 hex digest.
    Used for drift detection (compare project's recorded hash against current bundle's).
    """
    version: str
    files: dict[str, str]

    def hash_for(self, path: str) -> str | None:
        """Return the recorded sha256 for a bundle-relative path, or None if missing."""
        return self.files.get(path)


def validate_bundle(data: dict[str, Any]) -> BundleSchema:
    """Validate a bundle.yaml dict and return a BundleSchema.

    Raises ValueError on missing/malformed fields.
    """
    if "version" not in data:
        raise ValueError("bundle.yaml missing required field: version")
    if "files" not in data:
        raise ValueError("bundle.yaml missing required field: files")
    if not isinstance(data["files"], dict):
        raise ValueError("bundle.yaml files must be a mapping (path → sha256)")

    return BundleSchema(
        version=str(data["version"]),
        files={str(k): str(v) for k, v in data["files"].items()},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_schemas_bundle.py -v
```

Expected: All 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/schemas.py tests/test_schemas_bundle.py
git commit -m "feat: bundle.yaml schema with file hash index"
git push
```

---

## Task 4: File hashing utility

**Files:**
- Create: `src/agent_weiss/lib/hashing.py`
- Create: `tests/test_hashing.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_hashing.py`:

```python
"""Tests for file hashing utility."""
from pathlib import Path
from agent_weiss.lib.hashing import sha256_file, sha256_bytes


def test_sha256_bytes_known_vector():
    """sha256_bytes returns hex digest matching standard test vector."""
    assert sha256_bytes(b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_sha256_bytes_empty():
    """Empty input has known hash."""
    assert sha256_bytes(b"") == (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def test_sha256_file_roundtrip(tmp_path: Path):
    """sha256_file reads file content and matches sha256_bytes."""
    f = tmp_path / "x.txt"
    f.write_bytes(b"hello\n")
    assert sha256_file(f) == sha256_bytes(b"hello\n")


def test_sha256_file_streaming(tmp_path: Path):
    """sha256_file works for files larger than chunk size."""
    f = tmp_path / "big.bin"
    payload = b"x" * (1024 * 1024)  # 1 MiB
    f.write_bytes(payload)
    assert sha256_file(f) == sha256_bytes(payload)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_hashing.py -v
```

Expected: 4 tests FAIL on import.

- [ ] **Step 3: Implement hashing**

Create `src/agent_weiss/lib/hashing.py`:

```python
"""File and byte hashing utilities.

Used for prescribed_files content-addressing in .agent-weiss.yaml,
drift detection against bundle.yaml, and reconciliation.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

_CHUNK_SIZE = 64 * 1024


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hex sha256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return the lowercase hex sha256 of a file's contents.

    Streams in 64 KiB chunks; safe for large files.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_hashing.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/hashing.py tests/test_hashing.py
git commit -m "feat: sha256 hashing for files and bytes"
git push
```

---

## Task 5: State file (`.agent-weiss.yaml`) read/write

**Files:**
- Create: `src/agent_weiss/lib/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_state.py`:

```python
"""Tests for .agent-weiss.yaml read/write."""
from pathlib import Path
import pytest
from agent_weiss.lib.state import (
    State,
    read_state,
    write_state,
    PrescribedFileEntry,
)


def test_read_missing_returns_empty_state(tmp_path: Path):
    """Missing .agent-weiss.yaml yields an empty State (first-run scenario)."""
    state = read_state(tmp_path)
    assert state.profiles == []
    assert state.prescribed_files == {}
    assert state.bundle_version is None


def test_write_then_read_roundtrip(tmp_path: Path):
    """A state written and re-read is structurally identical."""
    original = State(
        bundle_version="0.0.1",
        profiles=["universal", "python"],
        prescribed_files={
            ".agent-weiss/policies/universal-docs.rego": PrescribedFileEntry(
                sha256="abc123",
                bundle_path="profiles/universal/domains/docs/controls/agents-md-present/policy.rego",
                last_synced="2026-04-14",
            ),
        },
    )
    write_state(tmp_path, original)
    loaded = read_state(tmp_path)
    assert loaded.bundle_version == "0.0.1"
    assert loaded.profiles == ["universal", "python"]
    assert ".agent-weiss/policies/universal-docs.rego" in loaded.prescribed_files


def test_write_preserves_unknown_keys(tmp_path: Path):
    """Round-trip preserves any unknown top-level keys (forward compatibility)."""
    state_path = tmp_path / ".agent-weiss.yaml"
    state_path.write_text(
        "version: 1\n"
        "bundle_version: '0.0.1'\n"
        "profiles: []\n"
        "future_field: keep_me\n"
    )
    state = read_state(tmp_path)
    write_state(tmp_path, state)
    content = state_path.read_text()
    assert "future_field" in content
    assert "keep_me" in content


def test_state_file_path_is_yaml_at_root(tmp_path: Path):
    """State file lives at <project_root>/.agent-weiss.yaml."""
    state = State(profiles=["universal"])
    write_state(tmp_path, state)
    assert (tmp_path / ".agent-weiss.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_state.py -v
```

Expected: 4 tests FAIL on import.

- [ ] **Step 3: Implement state I/O**

Create `src/agent_weiss/lib/state.py`:

```python
"""Read and write .agent-weiss.yaml at the project root.

The state file is the source of truth for prescribed-vs-custom file classification.
Round-trips with ruamel.yaml to preserve comments and unknown keys (forward-compat).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from ruamel.yaml import YAML

STATE_FILENAME = ".agent-weiss.yaml"
SCHEMA_VERSION = 1


@dataclass
class PrescribedFileEntry:
    """One entry in prescribed_files: hash + bundle origin + last sync date."""
    sha256: str
    bundle_path: str
    last_synced: str  # ISO date


@dataclass
class State:
    """In-memory representation of .agent-weiss.yaml.

    Only the fields the skeleton reads are typed here; unknown top-level keys
    are preserved verbatim via the _raw shadow dict for forward compatibility.
    """
    bundle_version: str | None = None
    profiles: list[str] = field(default_factory=list)
    prescribed_files: dict[str, PrescribedFileEntry] = field(default_factory=dict)
    _raw: dict = field(default_factory=dict, repr=False)


def _yaml() -> YAML:
    """Configured ruamel.yaml instance for round-trip preservation."""
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # avoid line-wrapping long values
    return y


def read_state(project_root: Path) -> State:
    """Read .agent-weiss.yaml from project root. Returns empty State if missing."""
    path = project_root / STATE_FILENAME
    if not path.exists():
        return State()

    yaml = _yaml()
    raw = yaml.load(path) or {}

    pf = {}
    for key, entry in (raw.get("prescribed_files") or {}).items():
        pf[str(key)] = PrescribedFileEntry(
            sha256=str(entry["sha256"]),
            bundle_path=str(entry["bundle_path"]),
            last_synced=str(entry["last_synced"]),
        )

    return State(
        bundle_version=raw.get("bundle_version"),
        profiles=list(raw.get("profiles") or []),
        prescribed_files=pf,
        _raw=dict(raw),
    )


def write_state(project_root: Path, state: State) -> None:
    """Write State back to .agent-weiss.yaml, preserving unknown keys.

    Strategy: start from state._raw (preserves comments + unknown fields),
    overlay typed fields. This is the source of forward compatibility.
    """
    path = project_root / STATE_FILENAME
    yaml = _yaml()

    out = dict(state._raw)
    out["version"] = SCHEMA_VERSION
    if state.bundle_version is not None:
        out["bundle_version"] = state.bundle_version
    out["profiles"] = state.profiles
    out["prescribed_files"] = {
        path_key: {
            "sha256": entry.sha256,
            "bundle_path": entry.bundle_path,
            "last_synced": entry.last_synced,
        }
        for path_key, entry in state.prescribed_files.items()
    }

    with path.open("w") as f:
        yaml.dump(out, f)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_state.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/state.py tests/test_state.py
git commit -m "feat: .agent-weiss.yaml read/write with ruamel.yaml round-trip"
git push
```

---

## Task 6: Bundle root resolution

**Files:**
- Create: `src/agent_weiss/lib/bundle.py`
- Create: `tests/test_bundle.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_bundle.py`:

```python
"""Tests for bundle root resolution."""
from pathlib import Path
import pytest
from agent_weiss.lib.bundle import resolve_bundle_root, BundleNotFoundError


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch):
    """Always start each test with AGENT_WEISS_BUNDLE unset, so external env doesn't leak in."""
    monkeypatch.delenv("AGENT_WEISS_BUNDLE", raising=False)


def test_resolve_via_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """AGENT_WEISS_BUNDLE env var takes precedence over probe order."""
    bundle = tmp_path / "my-bundle"
    bundle.mkdir()
    (bundle / "bundle.yaml").write_text("version: '0.0.1'\nfiles: {}\n")

    monkeypatch.setenv("AGENT_WEISS_BUNDLE", str(bundle))
    assert resolve_bundle_root() == bundle


def test_env_var_pointing_to_invalid_dir_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """If env var points somewhere without bundle.yaml, raise."""
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv("AGENT_WEISS_BUNDLE", str(empty))
    with pytest.raises(BundleNotFoundError, match="bundle.yaml"):
        resolve_bundle_root()


def test_resolve_via_probe(tmp_path: Path):
    """With env var unset, probe walks the candidate paths in order."""
    candidate = tmp_path / "fake-claude-plugins" / "yoselabs" / "agent-weiss"
    candidate.mkdir(parents=True)
    (candidate / "bundle.yaml").write_text("version: '0.0.1'\nfiles: {}\n")

    assert resolve_bundle_root(probe_paths=[candidate]) == candidate


def test_no_bundle_anywhere_raises():
    """If env var unset and probe finds nothing, raise."""
    with pytest.raises(BundleNotFoundError):
        resolve_bundle_root(probe_paths=[Path("/nonexistent/a"), Path("/nonexistent/b")])
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_bundle.py -v
```

Expected: 4 tests FAIL on import.

- [ ] **Step 3: Implement bundle resolution**

Create `src/agent_weiss/lib/bundle.py`:

```python
"""Resolve the agent-weiss bundle root.

Order:
1. AGENT_WEISS_BUNDLE env var (set by installers, manual override)
2. Probe known install locations (Claude → PyPI → npm)
"""
from __future__ import annotations
import os
import sys
from pathlib import Path


class BundleNotFoundError(RuntimeError):
    """Raised when no agent-weiss bundle can be located."""


def _default_probe_paths() -> list[Path]:
    """Default candidate paths for the bundle, in priority order.

    Claude Code marketplace install → PyPI install → npm install.
    """
    home = Path.home()
    paths: list[Path] = []

    # Claude Code marketplace
    paths.append(home / ".claude" / "plugins" / "yoselabs" / "agent-weiss")

    # PyPI install — share dir of the active Python prefix
    paths.append(Path(sys.prefix) / "share" / "agent-weiss")

    # npm install — common npm prefixes
    for npm_prefix in (
        Path("/usr/local"),
        home / ".local",
        home / ".npm-global",
    ):
        paths.append(npm_prefix / "share" / "agent-weiss")

    return paths


def resolve_bundle_root(probe_paths: list[Path] | None = None) -> Path:
    """Resolve the bundle root directory.

    Returns the first directory containing a bundle.yaml.
    Raises BundleNotFoundError if none found.
    """
    env = os.environ.get("AGENT_WEISS_BUNDLE")
    if env:
        candidate = Path(env)
        if (candidate / "bundle.yaml").exists():
            return candidate
        raise BundleNotFoundError(
            f"AGENT_WEISS_BUNDLE points to {candidate} but no bundle.yaml found there."
        )

    candidates = probe_paths if probe_paths is not None else _default_probe_paths()
    for c in candidates:
        if (c / "bundle.yaml").exists():
            return c

    raise BundleNotFoundError(
        "No agent-weiss bundle found. Set AGENT_WEISS_BUNDLE or install via "
        "Claude marketplace, PyPI, or npm."
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_bundle.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/bundle.py tests/test_bundle.py
git commit -m "feat: bundle root resolution via env var + probe order"
git push
```

---

## Task 7: `check.sh` output contract parser

**Files:**
- Create: `src/agent_weiss/lib/contract.py`
- Create: `tests/test_contract.py`

Per spec §3, every `check.sh` MUST emit one JSON line on stdout and exit with 0/1/127. This task implements the parser.

- [ ] **Step 1: Write the failing test**

Create `tests/test_contract.py`:

```python
"""Tests for the check.sh output contract parser."""
import pytest
from agent_weiss.lib.contract import (
    CheckResult,
    parse_check_output,
    Status,
    ContractError,
)


def test_parse_pass():
    stdout = '{"status": "pass", "findings_count": 0, "summary": "ruff: clean"}'
    result = parse_check_output(stdout=stdout, exit_code=0)
    assert isinstance(result, CheckResult)
    assert result.status is Status.PASS
    assert result.findings_count == 0
    assert result.summary == "ruff: clean"


def test_parse_fail_with_details():
    stdout = (
        '{"status": "fail", "findings_count": 8, "summary": "ruff: 8 issues", '
        '"details_path": "/tmp/x.log"}'
    )
    result = parse_check_output(stdout=stdout, exit_code=1)
    assert result.status is Status.FAIL
    assert result.findings_count == 8
    assert result.details_path == "/tmp/x.log"


def test_parse_setup_unmet():
    stdout = (
        '{"status": "setup-unmet", "summary": "ruff not installed", '
        '"install": "uv add --dev ruff"}'
    )
    result = parse_check_output(stdout=stdout, exit_code=127)
    assert result.status is Status.SETUP_UNMET
    assert result.install == "uv add --dev ruff"


def test_status_exit_code_mismatch_raises():
    """JSON status: pass with exit 1 is a contract violation."""
    stdout = '{"status": "pass", "findings_count": 0, "summary": "x"}'
    with pytest.raises(ContractError, match="exit code"):
        parse_check_output(stdout=stdout, exit_code=1)


def test_invalid_json_raises():
    with pytest.raises(ContractError, match="JSON"):
        parse_check_output(stdout="not json", exit_code=0)


def test_extra_lines_in_stdout_use_last_json_line():
    """Tools may print warnings to stdout; the contract line is the LAST JSON line."""
    stdout = (
        "warning: deprecated config\n"
        '{"status": "pass", "findings_count": 0, "summary": "ok"}\n'
    )
    result = parse_check_output(stdout=stdout, exit_code=0)
    assert result.status is Status.PASS


def test_unknown_status_raises():
    stdout = '{"status": "weird", "summary": "x"}'
    with pytest.raises(ContractError, match="status"):
        parse_check_output(stdout=stdout, exit_code=0)
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_contract.py -v
```

Expected: 7 tests FAIL on import.

- [ ] **Step 3: Implement contract parser**

Create `src/agent_weiss/lib/contract.py`:

```python
"""Parse check.sh output per the agent-weiss output contract.

Every check.sh emits exactly one JSON line on stdout (the last JSON line wins
if other lines precede it) and exits 0 / 1 / 127.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
from enum import Enum


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    SETUP_UNMET = "setup-unmet"


_STATUS_TO_EXIT = {
    Status.PASS: 0,
    Status.FAIL: 1,
    Status.SETUP_UNMET: 127,
}


class ContractError(ValueError):
    """check.sh output violates the agent-weiss contract."""


@dataclass(frozen=True)
class CheckResult:
    status: Status
    summary: str
    findings_count: int = 0
    install: str | None = None
    details_path: str | None = None


def parse_check_output(stdout: str, exit_code: int) -> CheckResult:
    """Parse a check.sh invocation's stdout + exit code into a CheckResult.

    Behavior:
    - The contract line is the LAST line of stdout that parses as JSON.
    - exit_code MUST match the JSON status (0=pass, 1=fail, 127=setup-unmet).
    - Mismatch or invalid JSON raises ContractError.
    """
    json_obj = _last_json_line(stdout)

    raw_status = json_obj.get("status")
    try:
        status = Status(raw_status)
    except ValueError as e:
        raise ContractError(f"unknown status: {raw_status!r}") from e

    expected_exit = _STATUS_TO_EXIT[status]
    if exit_code != expected_exit:
        raise ContractError(
            f"exit code {exit_code} does not match status {status.value} "
            f"(expected {expected_exit})"
        )

    return CheckResult(
        status=status,
        summary=str(json_obj.get("summary", "")),
        findings_count=int(json_obj.get("findings_count", 0)),
        install=json_obj.get("install"),
        details_path=json_obj.get("details_path"),
    )


def _last_json_line(stdout: str) -> dict:
    """Return the last line of stdout that parses as a JSON object."""
    last: dict | None = None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                last = obj
        except json.JSONDecodeError:
            continue
    if last is None:
        raise ContractError("no JSON contract line found in stdout")
    return last
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_contract.py -v
```

Expected: 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/contract.py tests/test_contract.py
git commit -m "feat: check.sh JSON output contract parser"
git push
```

---

## Task 8: Reconciliation algorithm (skeleton)

**Files:**
- Create: `src/agent_weiss/lib/reconcile.py`
- Create: `tests/test_reconcile.py`

This task implements the detection side of reconciliation (returns a typed report). The interactive prompts are a Plan 3 concern; here we just return what was found.

- [ ] **Step 1: Write the failing test**

Create `tests/test_reconcile.py`:

```python
"""Tests for the reconciliation detector."""
from pathlib import Path
from agent_weiss.lib.state import State, PrescribedFileEntry, write_state
from agent_weiss.lib.hashing import sha256_bytes
from agent_weiss.lib.reconcile import reconcile, ReconcileReport, Anomaly


def _setup_project_with_state(tmp_path: Path, prescribed_files: dict[str, PrescribedFileEntry]) -> Path:
    """Helper: create a project root with a state file."""
    state = State(
        bundle_version="0.0.1",
        profiles=["universal"],
        prescribed_files=prescribed_files,
    )
    write_state(tmp_path, state)
    return tmp_path


def test_clean_state_no_anomalies(tmp_path: Path):
    """If state and disk agree, report is empty."""
    policies_dir = tmp_path / ".agent-weiss" / "policies"
    policies_dir.mkdir(parents=True)
    policy = policies_dir / "x.rego"
    policy.write_bytes(b"package x\n")

    _setup_project_with_state(tmp_path, {
        ".agent-weiss/policies/x.rego": PrescribedFileEntry(
            sha256=sha256_bytes(b"package x\n"),
            bundle_path="profiles/universal/domains/docs/controls/x/policy.rego",
            last_synced="2026-04-14",
        ),
    })

    report = reconcile(tmp_path)
    assert isinstance(report, ReconcileReport)
    assert report.anomalies == []


def test_orphan_detected(tmp_path: Path):
    """File present in .agent-weiss/policies but not tracked → orphan."""
    policies_dir = tmp_path / ".agent-weiss" / "policies"
    policies_dir.mkdir(parents=True)
    (policies_dir / "stranger.rego").write_bytes(b"package stranger\n")

    _setup_project_with_state(tmp_path, {})

    report = reconcile(tmp_path)
    assert len(report.anomalies) == 1
    assert report.anomalies[0].kind == "orphan"
    assert report.anomalies[0].path.endswith("stranger.rego")


def test_ghost_detected(tmp_path: Path):
    """Tracked path missing from disk → ghost."""
    _setup_project_with_state(tmp_path, {
        ".agent-weiss/policies/missing.rego": PrescribedFileEntry(
            sha256="abc",
            bundle_path="profiles/x/y/z/policy.rego",
            last_synced="2026-04-14",
        ),
    })

    report = reconcile(tmp_path)
    assert len(report.anomalies) == 1
    assert report.anomalies[0].kind == "ghost"
    assert report.anomalies[0].path == ".agent-weiss/policies/missing.rego"


def test_locally_modified_detected(tmp_path: Path):
    """Tracked path with hash mismatch → locally_modified."""
    policies_dir = tmp_path / ".agent-weiss" / "policies"
    policies_dir.mkdir(parents=True)
    policy = policies_dir / "modded.rego"
    policy.write_bytes(b"package modded_local\n")  # different content

    _setup_project_with_state(tmp_path, {
        ".agent-weiss/policies/modded.rego": PrescribedFileEntry(
            sha256=sha256_bytes(b"package modded_original\n"),
            bundle_path="profiles/x/y/z/policy.rego",
            last_synced="2026-04-14",
        ),
    })

    report = reconcile(tmp_path)
    assert len(report.anomalies) == 1
    assert report.anomalies[0].kind == "locally_modified"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
uv run pytest tests/test_reconcile.py -v
```

Expected: 4 tests FAIL on import.

- [ ] **Step 3: Implement reconciliation detector**

Create `src/agent_weiss/lib/reconcile.py`:

```python
"""Detect anomalies between .agent-weiss.yaml state and project disk reality.

Returns a structured report. Interactive prompting (the user-facing 'what
should I do about this?' flow) is layered on top by skill.md / Plan 3.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from agent_weiss.lib.state import State, read_state
from agent_weiss.lib.hashing import sha256_file


AnomalyKind = Literal["orphan", "ghost", "locally_modified"]

POLICIES_DIR = ".agent-weiss/policies"


@dataclass(frozen=True)
class Anomaly:
    kind: AnomalyKind
    path: str
    detail: str = ""


@dataclass
class ReconcileReport:
    anomalies: list[Anomaly] = field(default_factory=list)


def reconcile(project_root: Path) -> ReconcileReport:
    """Compare state against disk; return a list of anomalies (no prompting)."""
    state = read_state(project_root)
    report = ReconcileReport()

    # 1. Detect ghosts (tracked but missing) and locally-modified (tracked, hash mismatch).
    for relative_path, entry in state.prescribed_files.items():
        full_path = project_root / relative_path
        if not full_path.exists():
            report.anomalies.append(Anomaly(
                kind="ghost",
                path=relative_path,
                detail=f"recorded sha256 {entry.sha256[:8]}, file missing",
            ))
            continue

        actual_hash = sha256_file(full_path)
        if actual_hash != entry.sha256:
            report.anomalies.append(Anomaly(
                kind="locally_modified",
                path=relative_path,
                detail=f"recorded {entry.sha256[:8]}, on disk {actual_hash[:8]}",
            ))

    # 2. Detect orphans (in policies dir, not tracked).
    policies_dir = project_root / POLICIES_DIR
    if policies_dir.exists():
        for entry_path in policies_dir.iterdir():
            if not entry_path.is_file():
                continue
            relative_path = str(entry_path.relative_to(project_root))
            if relative_path not in state.prescribed_files:
                report.anomalies.append(Anomaly(
                    kind="orphan",
                    path=relative_path,
                    detail="present on disk, not in prescribed_files",
                ))

    return report
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
uv run pytest tests/test_reconcile.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/agent_weiss/lib/reconcile.py tests/test_reconcile.py
git commit -m "feat: reconciliation detector for orphans/ghosts/locally-modified"
git push
```

---

## Task 9: First end-to-end control — `universal/docs/agents-md-present`

**Files:**
- Create: `profiles/universal/manifest.yaml`
- Create: `profiles/universal/domains/docs/controls/agents-md-present/prescribed.yaml`
- Create: `profiles/universal/domains/docs/controls/agents-md-present/check.sh`
- Create: `profiles/universal/domains/docs/controls/agents-md-present/instruct.md`
- Create: `fixtures/profiles/universal/domains/docs/controls/agents-md-present/pass/AGENTS.md`
- Create: `fixtures/profiles/universal/domains/docs/controls/agents-md-present/pass/README.md`
- Create: `fixtures/profiles/universal/domains/docs/controls/agents-md-present/fail/README.md`
- Create: `tests/test_fixture_runner.py`

This control verifies that `AGENTS.md` exists at the project root. It's the simplest possible control — just a file existence check — but it exercises the full fixture pipeline.

- [ ] **Step 1: Write the failing fixture-runner test**

Create `tests/test_fixture_runner.py`:

```python
"""Run check.sh against pass/ and fail/ fixtures, validate via the contract parser.

This is the canonical pattern for testing every control in agent-weiss:
each control ships with a pass/ fixture (control should report pass) and a
fail/ fixture (control should report fail or setup-unmet). Both stdout and
exit code are validated through parse_check_output, which enforces the
contract (status field present, status matches exit code, valid JSON).
"""
from __future__ import annotations
import subprocess
from pathlib import Path

import pytest

from agent_weiss.lib.contract import Status, parse_check_output

REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILES = REPO_ROOT / "profiles"
FIXTURES = REPO_ROOT / "fixtures"


def _discover_controls() -> list[Path]:
    """Find every control with both pass/ and fail/ fixtures."""
    discovered: list[Path] = []
    if not FIXTURES.exists():
        return discovered
    for control_dir in FIXTURES.rglob("controls/*"):
        if not control_dir.is_dir():
            continue
        if (control_dir / "pass").is_dir() and (control_dir / "fail").is_dir():
            discovered.append(control_dir)
    return discovered


def _control_check_sh(fixture_control_dir: Path) -> Path:
    """Translate a fixtures path to the corresponding profiles check.sh path."""
    relative = fixture_control_dir.relative_to(FIXTURES)
    return PROFILES / relative / "check.sh"


@pytest.mark.parametrize("fixture_control_dir", _discover_controls(), ids=lambda p: str(p.relative_to(FIXTURES)))
def test_control_passes_on_pass_fixture(fixture_control_dir: Path):
    """Pass fixture must produce status=pass via the contract parser."""
    check_sh = _control_check_sh(fixture_control_dir)
    assert check_sh.exists(), f"missing check.sh at {check_sh}"

    pass_dir = fixture_control_dir / "pass"
    result = subprocess.run(
        ["sh", str(check_sh)],
        cwd=pass_dir,
        capture_output=True,
        text=True,
    )
    parsed = parse_check_output(stdout=result.stdout, exit_code=result.returncode)
    assert parsed.status is Status.PASS, (
        f"expected status=pass in {pass_dir}, got {parsed.status.value}\n"
        f"summary={parsed.summary!r}"
    )


@pytest.mark.parametrize("fixture_control_dir", _discover_controls(), ids=lambda p: str(p.relative_to(FIXTURES)))
def test_control_fails_on_fail_fixture(fixture_control_dir: Path):
    """Fail fixture must produce status=fail OR status=setup-unmet via the contract parser."""
    check_sh = _control_check_sh(fixture_control_dir)
    assert check_sh.exists(), f"missing check.sh at {check_sh}"

    fail_dir = fixture_control_dir / "fail"
    result = subprocess.run(
        ["sh", str(check_sh)],
        cwd=fail_dir,
        capture_output=True,
        text=True,
    )
    parsed = parse_check_output(stdout=result.stdout, exit_code=result.returncode)
    assert parsed.status in (Status.FAIL, Status.SETUP_UNMET), (
        f"expected status=fail or setup-unmet in {fail_dir}, got {parsed.status.value}\n"
        f"summary={parsed.summary!r}"
    )
```

- [ ] **Step 2: Run test to verify it fails (no fixtures yet → 0 tests collected)**

Run:
```bash
uv run pytest tests/test_fixture_runner.py -v
```

Expected: `no tests ran` or `collected 0 items`. This is fine — the runner is parametric, and we'll add fixtures next.

- [ ] **Step 3: Create the universal profile manifest**

Create `profiles/universal/manifest.yaml`:

```yaml
profile: universal
description: Standards that apply to any project, regardless of language or framework.
domains:
  - docs
  - security
  - vcs
  - project-structure
```

- [ ] **Step 4: Create the control's prescribed.yaml**

Create `profiles/universal/domains/docs/controls/agents-md-present/prescribed.yaml`:

```yaml
id: universal.docs.agents-md-present
version: 1
what: |
  Project has an AGENTS.md file at the repository root.
why: |
  AGENTS.md is the cross-tool standard for instructing AI coding agents
  (Codex, OpenCode, and others). Present alongside CLAUDE.md, it makes the
  project legible to non-Claude agents.
applies_to:
  - any
```

- [ ] **Step 5: Create the control's check.sh**

Create `profiles/universal/domains/docs/controls/agents-md-present/check.sh`:

```sh
#!/bin/sh
# universal.docs.agents-md-present
# Exit 0 + status:pass if AGENTS.md exists at the repo root.
# Exit 1 + status:fail otherwise.

if [ -f AGENTS.md ]; then
  printf '%s\n' '{"status": "pass", "findings_count": 0, "summary": "AGENTS.md present"}'
  exit 0
else
  printf '%s\n' '{"status": "fail", "findings_count": 1, "summary": "AGENTS.md missing at project root"}'
  exit 1
fi
```

Run:
```bash
chmod +x profiles/universal/domains/docs/controls/agents-md-present/check.sh
```

- [ ] **Step 6: Create the control's instruct.md**

Create `profiles/universal/domains/docs/controls/agents-md-present/instruct.md`:

```markdown
# Why AGENTS.md

`AGENTS.md` is the emerging cross-tool convention for instructing AI coding agents on
project conventions, commands, gotchas, and the development workflow. Codex, OpenCode,
and other agents look for it the way Claude Code looks for `CLAUDE.md`.

## What goes in it

A short prose document covering:
- How to run the dev loop (`make dev`, `pnpm dev`, etc.)
- How to run tests (`make test`, `pytest`, etc.)
- Project conventions (one bullet per: file layout, naming, etc.)
- Known gotchas the agent will hit if it doesn't know about them

## Relationship to CLAUDE.md

Both should exist when a project supports multiple agents. Content can be largely shared;
keep tool-specific instructions in their respective files.

## When to override

If your team explicitly does not use Codex/OpenCode and only uses Claude Code, declare
an override in `.agent-weiss.yaml` with a brief reason.
```

- [ ] **Step 7: Create the pass fixture**

Create `fixtures/profiles/universal/domains/docs/controls/agents-md-present/pass/AGENTS.md`:

```markdown
# Agent instructions for this fixture project

Run `make test` to verify changes.
```

Create `fixtures/profiles/universal/domains/docs/controls/agents-md-present/pass/README.md`:

```markdown
# Pass fixture for universal.docs.agents-md-present
```

- [ ] **Step 8: Create the fail fixture**

Create `fixtures/profiles/universal/domains/docs/controls/agents-md-present/fail/README.md`:

```markdown
# Fail fixture for universal.docs.agents-md-present

This fixture intentionally omits AGENTS.md.
```

- [ ] **Step 9: Run the fixture runner**

Run:
```bash
uv run pytest tests/test_fixture_runner.py -v
```

Expected: 2 tests PASS — `test_control_passes_on_pass_fixture[profiles/universal/domains/docs/controls/agents-md-present]` and `test_control_fails_on_fail_fixture[...]`.

- [ ] **Step 10: Commit**

```bash
git add profiles/ fixtures/ tests/test_fixture_runner.py
git commit -m "feat: first end-to-end control + fixture runner

universal.docs.agents-md-present is the canonical example:
- prescribed.yaml + check.sh + instruct.md
- pass/ and fail/ fixtures
- pytest parametric runner walks every control fixture pair"
git push
```

---

## Task 10: Validate prescribed.yaml + check.sh present for every control

**Files:**
- Create: `tests/test_control_completeness.py`

This is a self-test that prevents shipping a control missing required artifacts.

- [ ] **Step 1: Write the failing test**

Create `tests/test_control_completeness.py`:

```python
"""Self-test: every control directory has the required artifacts.

Required: prescribed.yaml, instruct.md.
Required for non-judgment-only controls: check.sh.
Required for fixture-tested controls: pass/ and fail/ fixtures.

Validation also runs prescribed.yaml through the schema validator.
"""
from __future__ import annotations
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from agent_weiss.lib.schemas import validate_prescribed


REPO_ROOT = Path(__file__).resolve().parent.parent
PROFILES = REPO_ROOT / "profiles"
FIXTURES = REPO_ROOT / "fixtures"


def _all_control_dirs() -> list[Path]:
    """Every directory under profiles/*/domains/*/controls/*/."""
    out: list[Path] = []
    for control_dir in PROFILES.rglob("controls/*"):
        if control_dir.is_dir():
            out.append(control_dir)
    return out


@pytest.mark.parametrize("control_dir", _all_control_dirs(), ids=lambda p: str(p.relative_to(PROFILES)))
def test_control_has_prescribed_yaml(control_dir: Path):
    p = control_dir / "prescribed.yaml"
    assert p.exists(), f"{control_dir} missing prescribed.yaml"
    yaml = YAML(typ="safe")
    data = yaml.load(p)
    assert data is not None, f"{p} is empty"
    validate_prescribed(data)  # raises on schema violation


@pytest.mark.parametrize("control_dir", _all_control_dirs(), ids=lambda p: str(p.relative_to(PROFILES)))
def test_control_has_instruct_md(control_dir: Path):
    p = control_dir / "instruct.md"
    assert p.exists(), f"{control_dir} missing instruct.md"
    assert p.read_text().strip(), f"{p} is empty"


@pytest.mark.parametrize("control_dir", _all_control_dirs(), ids=lambda p: str(p.relative_to(PROFILES)))
def test_control_has_fixtures(control_dir: Path):
    """Every control should have pass/ and fail/ fixtures."""
    relative = control_dir.relative_to(PROFILES)
    fixture_dir = FIXTURES / relative
    assert (fixture_dir / "pass").is_dir(), f"missing pass fixture at {fixture_dir / 'pass'}"
    assert (fixture_dir / "fail").is_dir(), f"missing fail fixture at {fixture_dir / 'fail'}"
```

- [ ] **Step 2: Run tests**

Run:
```bash
uv run pytest tests/test_control_completeness.py -v
```

Expected: All tests PASS for the single control we have so far.

- [ ] **Step 3: Commit**

```bash
git add tests/test_control_completeness.py
git commit -m "test: every control has prescribed.yaml + instruct.md + fixtures"
git push
```

---

## Task 11: Skill entry point — `skill.md` scaffolding

**Files:**
- Create: `.claude/skills/agent-weiss/SKILL.md`
- Create: `bundle.yaml` (initial — manifest will be regenerated by Plan 5)

The Claude Code skill's markdown is the agent-facing description of WHAT to do at each step. Plan 5 will package this for distribution; for now we hand-author it so the loop is testable end-to-end via Claude Code locally.

- [ ] **Step 1: Create the skill manifest directory**

Run:
```bash
mkdir -p .claude/skills/agent-weiss
```

- [ ] **Step 2: Create initial `bundle.yaml`**

Create `bundle.yaml` at the repo root:

```yaml
version: "0.0.1"
files: {}  # populated by Plan 5 at packaging time
```

This is a placeholder. The packaging plan (Plan 5) will rewrite this file with per-file SHA index at build time. For Task 11 the file just needs to exist so the bundle resolver finds something.

- [ ] **Step 3: Author the skill markdown**

Create `.claude/skills/agent-weiss/SKILL.md`:

```markdown
---
name: agent-weiss
description: |
  Audits and sets up codebases to be agent-ready. Detects the project's stack,
  matches applicable profiles, gap-analyzes against prescribed standards, applies
  approved changes, and produces Setup + Quality scores. Run this whenever you
  want to confirm a project is configured well for AI coding agents.
---

# agent-weiss

You are running the **agent-weiss skill**: a knowledge companion that audits
codebases for agent-readiness and sets up missing infrastructure with explicit
user approval.

## Bundle root

The agent-weiss bundle (profiles, controls, helper scripts) is resolved via:

1. `$AGENT_WEISS_BUNDLE` env var (manual override)
2. `~/.claude/plugins/yoselabs/agent-weiss/` (Claude marketplace install)
3. `<python-prefix>/share/agent-weiss/` (PyPI install)
4. `<npm-prefix>/share/agent-weiss/` (npm install)

When in doubt, the bundle resolver can be invoked directly:

```python
from agent_weiss.lib.bundle import resolve_bundle_root
print(resolve_bundle_root())
```

This prints the resolved root or raises `BundleNotFoundError`.

## Standard run loop

Follow these steps every time the user invokes the skill. Do not skip steps.

### 1. Detect

Read `<project_root>/.agent-weiss.yaml` if it exists. Note the `bundle_version`,
`profiles`, and `prescribed_files` map. If absent, treat this as a first run.

Scan the project root for stack signals:
- `pyproject.toml` → python profile candidate
- `package.json` → typescript profile candidate
- `Dockerfile` → docker profile candidate (deferred to v2; surface as detected
  but not yet supported)

### 2. Reconcile

Invoke the reconciliation detector:

```python
from pathlib import Path
from agent_weiss.lib.reconcile import reconcile
report = reconcile(Path("<project_root>"))
for anomaly in report.anomalies:
    # surface to user
    ...
```

> Plan 1 limitation: orphan detection only scans `.agent-weiss/policies/`. Files prescribed at other paths (e.g., `.pre-commit-config.yaml`) get ghost detection but not orphan detection. Plan 3 will broaden this.

For each anomaly returned (orphan / ghost / locally_modified), prompt the user
with the appropriate choice set per spec §6 "Reconciliation." Do not silently
delete or reclassify files.

### 3. Confirm profiles

Tell the user: "I detected python + docker. Add or remove any?" Honor their
answer. Persist confirmed profiles in `.agent-weiss.yaml`.

### 4. Setup phase

For each control in each confirmed profile, gap-analyze: is the prescribed
state present? If not, propose the change.

Show the user the full setup plan, batched by domain. Use the verbs:
`approve all`, `approve <domain>`, `<numbers>`, `skip <numbers>`,
`explain <N>`, `dry-run`, `cancel`. Apply approved changes, backing up any
overwritten file to `.agent-weiss/backups/<timestamp>/`.

### 5. Verify phase

For each control, run its `check.sh`. Parse the JSON output line per the
contract:
- `status: pass` (exit 0) — control satisfied
- `status: fail` (exit 1) — Quality issue, surface findings_count and summary
- `status: setup-unmet` (exit 127) — control infrastructure missing, surface
  the install command and treat as Setup-unmet

### 6. Score and report

Compute per spec §7:
- Setup score: per-control 100/0, per-domain average, total average of domains.
  Override-with-reason counts as 100.
- Quality score: per-control 100/0, exclude setup-unmet controls.

Print the report in the format shown in spec §7.

### 7. Update state

Write the updated `.agent-weiss.yaml` with: confirmed profiles, prescribed_files
map (with fresh sha256 hashes for any files copied this run), scores, drift,
last_scan / last_setup timestamps.

## What you must NEVER do

- Auto-install tools (`brew`, `uv`, `pnpm`, `apt`). Always instruct the user.
- Silently overwrite files. Always back up first.
- Treat header comments as load-bearing. State file is source of truth.
- Skip the reconciliation step. It must run before setup phase.

## Cross-references

- Spec: `docs/spec.md`
- Helper modules: `src/agent_weiss/lib/`
- Profiles: `profiles/`
- Fixtures (for skill self-tests, not for users): `fixtures/`
```

- [ ] **Step 4: Verify the skill is locally discoverable**

Run:
```bash
ls -la .claude/skills/agent-weiss/SKILL.md && cat bundle.yaml
```

Expected: SKILL.md exists, bundle.yaml prints `version: "0.0.1"` and `files: {}`.

> **Note:** The skill.md describes what to invoke (Python helpers) but does not yet implement the full setup-phase logic. That comes in Plan 3 (Setup Workflow & Approval UX) and Plan 4 (Verify Workflow & Scoring). Plan 1's skill.md is the scaffold that Plans 3-4 will flesh out.

- [ ] **Step 5: Commit**

```bash
git add bundle.yaml .claude/skills/agent-weiss/SKILL.md
git commit -m "feat: skill.md scaffolding + initial bundle.yaml placeholder"
git push
```

---

## Task 12: CI workflow — run all tests on every push

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: latest

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install deps
        run: uv sync

      - name: Install conftest (required by Plan 2 controls)
        run: |
          CONFTEST_VERSION=0.56.0
          curl -sL "https://github.com/open-policy-agent/conftest/releases/download/v${CONFTEST_VERSION}/conftest_${CONFTEST_VERSION}_Linux_x86_64.tar.gz" \
            | sudo tar xz -C /usr/local/bin conftest

      - name: Run pytest
        run: uv run pytest -v
```

> Note: conftest is installed proactively. Plan 1 ships zero Rego policies, but Plan 2 adds them, and a CI break on the first Plan 2 PR would be confusing. Cheap to install now.

- [ ] **Step 2: Commit and verify CI passes**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run pytest on every push and PR"
git push
```

Then check the run:

```bash
gh run list --repo yoselabs/agent-weiss --limit 1
```

Expected: workflow `CI` queued or in_progress. After it completes:

```bash
gh run watch
```

Expected: `completed / success` for the most recent run.

If failure, inspect with `gh run view --log-failed` and fix before proceeding to Task 13.

---

## Task 13: Self-review against the spec + roadmap

**Files:**
- None (review-only task)

- [ ] **Step 1: Walk the spec sections and confirm Plan 1 coverage**

Open the local copy `/Users/iorlas/Workspaces/agent-weiss/docs/spec.md` (a copy was made in Task 0). The canonical spec lives in the agent-harness repo at `/Users/iorlas/Workspaces/agent-harness/docs/superpowers/specs/2026-04-14-agent-weiss-design.md` — refer there if any conflict.

Verify each major spec section has a corresponding implementation:

| Spec section | Plan 1 task |
|---|---|
| §1 Product / platform / distribution | Distribution is Plan 5; platform supported via POSIX shell |
| §2 Scope (v1 profiles) | universal profile manifest in Task 9 |
| §3 Architecture / output contract | Tasks 7 + 9 |
| §4 State file schema | Tasks 5, 8 |
| §5 Source classification | Tasks 5, 8 |
| §6 User loop | Skill.md in Task 11 |
| §7 Two scores | Score formula deferred to Plan 4 |
| §8 Safety mechanics | Backups + dry-run deferred to Plan 3 |
| §9 Migration from agent-harness | Migration deferred to Plan 2 |
| §11 Open questions | Schemas locked in Tasks 2-3 |

This is a sanity check. If any required-for-MVP piece is missing, add a task before declaring Plan 1 complete.

- [ ] **Step 2: Update roadmap status (cross-repo edit)**

The roadmap lives in the **agent-harness** repo, not agent-weiss. Open the absolute path:

`/Users/iorlas/Workspaces/agent-harness/docs/superpowers/plans/2026-04-14-agent-weiss-roadmap.md`

Update Plan 1 status from `Active` to `Done` in the Plan sequence table. Then commit and push from the agent-harness repo:

```bash
cd /Users/iorlas/Workspaces/agent-harness
git add docs/superpowers/plans/2026-04-14-agent-weiss-roadmap.md
git commit -m "roadmap: mark agent-weiss Plan 1 (Foundations) complete"
git push
```

- [ ] **Step 3: Tag the milestone**

Run:
```bash
cd /Users/iorlas/Workspaces/agent-weiss
git tag -a foundations-mvp -m "Plan 1 complete: foundations + first end-to-end control"
git push origin foundations-mvp
```

---

## Plan-completion checklist

Before declaring Plan 1 done:
- [ ] All 13 tasks committed and pushed
- [ ] CI green on `main`
- [ ] `uv run pytest -v` passes locally with at least one fixture-runner test (the universal.docs.agents-md-present pair)
- [ ] Bundle resolution sanity check passes — run from the agent-weiss repo root:
  ```bash
  AGENT_WEISS_BUNDLE=$(pwd) uv run python -c "from agent_weiss.lib.bundle import resolve_bundle_root; print(resolve_bundle_root())"
  ```
  Expected: prints the absolute path to the agent-weiss repo root.
- [ ] Roadmap updated in agent-harness repo: Plan 1 → Done, Plan 2 → Active
- [ ] No TODO / TBD / "fix later" markers in code
