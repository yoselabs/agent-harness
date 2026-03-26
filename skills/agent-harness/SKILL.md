---
name: agent-harness
description: "Deterministic quality gates for AI agents. Use when setting up a project, when lint fails, or when agent output is noisy. Triggers: 'set up harness', 'check harness', new project, first commit."
---

# Agent Harness

Deterministic controls (linters, type checkers, formatters, coverage gates) that constrain AI agent behavior automatically.

Run `agent-harness --help` for available commands and flags.

## Commands

- `agent-harness init` — Diagnose harness setup: check tools, config quality, missing files (report mode)
- `agent-harness init --apply` — Apply auto-fixes and create missing config files
- `agent-harness lint` — Run all harness checks (fast, pass/fail, blocks commits)
- `agent-harness lint --all` — Lint all subprojects (monorepo mode)
- `agent-harness fix` — Auto-fix what's fixable (ruff format/check --fix), then lint
- `agent-harness detect` — Show detected stacks and subprojects

## When to Use

- Setting up a new project — run `agent-harness init` then `agent-harness init --apply`
- Lint failures or noisy agent output — run `agent-harness lint`
- Monorepo with multiple subprojects — run `agent-harness lint --all`
- Checking config quality after changes — run `agent-harness init`
- User says "set up harness", "check harness", "apply harness"

## When NOT to Use

- Business logic, architecture, or domain modeling
- Deployment operations (use deployment-platform skill)
- Fixing one specific tool config (help directly)

## How It Works

Agent-harness auto-detects project stacks (Python, JavaScript, Docker, Dokploy) and runs the right checks. Every error message is actionable — read it, fix it, re-lint.

### Two modes, clean separation

- **lint** — Rego policies via conftest. Only `deny` rules. Fast enforcement every commit. "Is this gate broken?"
- **init** — Python setup checks with fix capability. Critical issues + recommendations. On-demand diagnostic. "Is this gate configured well?"

When a user challenges a lint rule, read the WHY block from the Rego policy file. When a user challenges an init recommendation, check `presets/*/setup.py` for the check logic.

## Guidance

Read these files when writing new Docker or Python code:

- **`docker-guidance.md`** — healthcheck recipes, dependency chains, migration patterns, config file strategy, base image selection
- **`python-guidance.md`** — why each pyproject.toml knob matters
