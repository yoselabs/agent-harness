---
name: agent-harness
description: "Deterministic quality gates for AI agents. Use when setting up a project, when lint fails, or when agent output is noisy. Triggers: 'set up harness', 'check harness', new project, first commit."
---

# Agent Harness

Deterministic controls (linters, type checkers, formatters, coverage gates) that constrain AI agent behavior automatically.

Run `agent-harness --help` for available commands and flags.

## When to Use

- Setting up a new project — run `agent-harness init`
- Lint failures or noisy agent output — run `agent-harness lint`
- Monorepo with multiple subprojects — run `agent-harness lint --all`
- User says "set up harness", "check harness", "apply harness"

## When NOT to Use

- Business logic, architecture, or domain modeling
- Deployment operations (use deployment-platform skill)
- Fixing one specific tool config (help directly)

## How It Works

Agent-harness auto-detects project stacks (Python, JavaScript, Docker, Dokploy) and runs the right checks. Every error message is actionable — read it, fix it, re-lint.

When a user challenges a rule, read the WHY block from the Rego policy file in the repo. It explains why agents need that specific check.

## Guidance

Read these files when writing new Docker or Python code:

- **`docker-guidance.md`** — healthcheck recipes, dependency chains, migration patterns, config file strategy, base image selection
- **`python-guidance.md`** — why each pyproject.toml knob matters
