# agent-harness — AI-first harness engineering CLI

Deterministic controls for AI agents. Detects project stacks, runs checks, initializes configs.

## Dev Commands

- Run tests: `uv run pytest tests/`
- Lint: `uv run ruff check src/ tests/`
- Fix: `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/`
- Run CLI: `uv run agent-harness --help`
- Run CLI on aggre: `cd ~/Workspaces/aggre && uv run --project ~/Workspaces/agent-harness agent-harness lint`

## Architecture

- `cli.py` — Click CLI, delegates to modules
- `detect.py` — Stack detection from file presence
- `config.py` — .agent-harness.yml parsing
- `runner.py` — Subprocess execution with unified output
- `checks/` — One module per check tool
- `policies/` — Bundled Rego policies (source of truth)

## Never

- Never embed tool binaries (ruff, hadolint, conftest) — require them installed
- Never run checks in Docker — must be <1s local
