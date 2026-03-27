---
name: agent-harness
description: "Deterministic quality gates for AI agents. Use when setting up a project, when lint fails, or when agent output is noisy. Triggers: 'set up harness', 'check harness', new project, first commit."
---

# Agent Harness

Deterministic controls (linters, type checkers, formatters, coverage gates) that constrain AI agent behavior automatically.

## Setup Workflow (when user says "set up harness", "apply harness", or first time in a project)

This is a committed action. Once the user asks for setup, execute the full plan — don't stop to ask permission at each step. Present a summary at the end.

### Step 1: Diagnose

```bash
agent-harness detect          # see what stacks are detected
agent-harness init            # diagnose issues (report mode)
```

### Step 1.5: Audit existing Makefiles and pre-commit hooks

Before applying, read every Makefile in the project (root + all subprojects). Skip dependency directories (node_modules, .venv, vendor, dist). Also read `.pre-commit-config.yaml` if it exists.

**What to look for:**

1. **Duplicated work.** If a subproject Makefile runs `ruff`, `ty`, `biome`, `hadolint`, or any tool that agent-harness already runs — that's duplication. The subproject's `make lint` should delegate to `agent-harness lint`, not invoke tools directly. Flag every instance.

2. **Bypassed tools.** If a Makefile runs `ruff` but NOT `ty` (or vice versa), an agent using that Makefile skips a gate. This is how type errors slip through — the agent runs the local `make lint`, gets a pass from ruff alone, and commits broken code.

3. **Conflicting fix targets.** If a subproject's `make fix` runs `ruff format` but the root's `make fix` runs `agent-harness fix` (which also runs ruff), files may be formatted twice or with conflicting configs.

4. **Missing delegation.** The root Makefile should call `agent-harness lint` (not individual tools). Subproject Makefiles should either delegate to `agent-harness lint` or to the root's `make lint` — never run tools independently.

5. **Pre-commit hook misalignment.** If `.pre-commit-config.yaml` runs `make lint` but the Makefile's lint target doesn't include agent-harness, the hook is bypassed. The hook should run `make lint` and `make lint` should run `agent-harness lint`.

6. **Stale targets.** Bootstrap targets that install tools agent-harness manages, test targets with different flags than what's in pyproject.toml, etc.

**What to do with findings:**

- Present all findings as a numbered list before applying fixes
- For each finding, state what's wrong and what the fix should be
- Propose Makefile rewrites that consolidate to agent-harness
- Execute the fixes — don't ask permission for each one
- If a subproject Makefile has non-lint targets (test, deploy, migrate) that are fine, leave those alone — only fix the lint/fix/check targets

**Example of a bad subproject Makefile:**
```makefile
lint:
    @uv run ruff format --check
    @uv run ruff check
    @uv run ty check     # <- agent-harness already runs all three
fix:
    uv run ruff check --fix
    uv run ruff format   # <- agent-harness fix does this
```

**Example of a good subproject Makefile:**
```makefile
lint:
    @agent-harness lint
fix:
    @agent-harness fix
```

### Step 2: Apply fixes

```bash
agent-harness init --apply    # auto-fix config + create missing files
```

### Step 3: Install pre-commit hooks

```bash
prek install                  # or: pre-commit install
```

If prek fails with "core.hooksPath set":
```bash
git config --unset-all --local core.hooksPath
prek install
```

If neither prek nor pre-commit is available, tell the user to install one:
`brew install prek` or `pip install pre-commit`.

### Step 4: Verify

```bash
make lint                     # must pass — if it doesn't, fix issues
```

### Step 5: Commit

Commit all generated/modified config files (`.agent-harness.yml`, `.yamllint.yml`, `.pre-commit-config.yaml`, `.gitignore` changes, `Makefile`).

### Step 6: Report

Present a clear summary of what was done, what passed, and any remaining issues that need manual attention. Do NOT ask "want me to fix these?" — list what you will fix and do it. Only stop for issues that require a human decision (e.g., choosing a coverage threshold).

## Commands

- `agent-harness init` — Diagnose harness setup (report mode)
- `agent-harness init --apply` — Apply auto-fixes and create missing config files
- `agent-harness lint` — Run all harness checks (fast, pass/fail, blocks commits)
- `agent-harness lint --all` — Lint all subprojects (monorepo mode)
- `agent-harness fix` — Auto-fix what's fixable (ruff format/check --fix), then lint
- `agent-harness detect` — Show detected stacks and subprojects

## When to Use

- Setting up a new project — run the **Setup Workflow** above
- Lint failures — run `agent-harness lint`, read error messages, fix issues
- Monorepo with multiple subprojects — run `agent-harness lint --all`
- Checking config quality after changes — run `agent-harness init`

## When NOT to Use

- Business logic, architecture, or domain modeling
- Deployment operations (use deployment-platform skill)
- Fixing one specific tool config (help directly)

## How It Works

Agent-harness auto-detects project stacks (Python, JavaScript, Docker, Dokploy) and runs the right checks. Every error message is actionable — read it, fix it, re-lint.

### Two modes, clean separation

- **lint** — Fast enforcement every commit. "Is this gate broken?" Checks: ruff, ty, conftest policies, yamllint, file length, gitignore tracked files, pre-commit hooks.
- **init** — On-demand diagnostic. "Is this gate configured well?" Checks config quality, gitignore completeness against github/gitignore templates, missing tools.

When a user challenges a lint rule, read the WHY block from the check file or Rego policy. When a user challenges an init recommendation, check `presets/*/setup.py` for the check logic.

## Monorepo Support

- `agent-harness lint --all` discovers subprojects and runs checks in each
- Git root is resolved automatically — gitignore and pre-commit checks use the repo root, not the subproject directory
- Each subproject can have its own `.agent-harness.yml` for stack overrides

## Guidance

Read these files when writing new Docker or Python code:

- **`docker-guidance.md`** — healthcheck recipes, dependency chains, migration patterns, config file strategy, base image selection
- **`python-guidance.md`** — why each pyproject.toml knob matters
