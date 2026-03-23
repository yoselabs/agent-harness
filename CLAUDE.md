# agent-harness

Deterministic quality gates for AI-assisted development. This project IS a harness — it enforces its own rules.

## Dev Commands

```bash
make lint          # agent-harness lint (runs all checks)
make fix           # agent-harness fix (auto-fix, then lint)
make test          # pytest + conftest verify (all tests)
```

Install dev deps: `uv sync`

## Setup

```bash
uv tool install -e .          # install CLI globally from source
uv sync                       # install dev deps (ruff, ty, pytest)
agent-harness lint             # verify everything passes
```

## Architecture

```
src/agent_harness/
  cli.py               — Click CLI: detect, init, lint, fix
  config.py            — .agent-harness.yml parsing, HarnessConfig dataclass
  detect.py            — Stack detection orchestrator (scans subdirs too)
  runner.py            — Subprocess execution, CheckResult, tool_available()
  exclusions.py        — File exclusion patterns (lock files, build output)
  workspace.py         — Discover subproject roots (.agent-harness.yml scanning)
  lint.py              — Check pipeline (universal → per-stack), lint_all for monorepos
  fix.py               — Auto-fix (ruff, biome), fix_all for monorepos
  init/                — Scaffolding (configs, Makefile, templates)
  stacks/
    universal/         — Always runs: yamllint, gitignore, JSON, file length
    python/            — ruff, ty, conftest on pyproject.toml
    javascript/        — Biome, framework type checker, conftest on package.json
    docker/            — hadolint, conftest on Dockerfile + compose
    dokploy/           — conftest for Traefik/Dokploy conventions
  policies/            — Rego policies (bundled in package). Each has WHAT/WHY/FIX.

skills/agent-harness/  — Claude Code plugin (SKILL.md + guidance docs)
```

## Conventions

- One check per file, with WHAT/WHY/WITHOUT IT/FIX/REQUIRES docstring
- One Rego policy per file, with `_test.rego` sibling
- Tests use `tmp_path` fixtures, mock subprocesses via `monkeypatch`
- Tool fallback: `shutil.which()` → `uv run` (Python) or `npx` (JS)
- `import rego.v1` and `if` keyword required in all Rego files

## Never

- Never embed tool binaries — require them installed externally
- Never run checks in Docker — must be <500ms local
