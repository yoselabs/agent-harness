# Roadmap

## Done (v0.1 — MVP)

- CLI commands: detect, lint, fix, init, audit
- 32 Rego policies across Dockerfile, Compose, Python, .gitignore
- Stack detection from file presence (Python, Docker)
- `.agent-harness.yml` config with auto-detection fallback
- Tool fallback — `uv run ruff`/`ty` when not in PATH
- JSON file validation via conftest parse
- Tested on real project (aggre), <1s execution

## Done (v0.1.1 — JS stack + universal fixes)

- **JavaScript/TypeScript stack** — Biome lint+format, framework-aware type checking (astro check > next lint > tsc), package.json Rego policies (engines, type:module, no wildcards)
- **File exclusion system** — `exclude:` in config + built-in defaults (lock files, build output, node_modules, archives). Wired into yamllint, conftest-json, file-length.
- **Stack-conditional gitignore** — .env universal, .venv/__pycache__ Python-only, node_modules/dist JS-only. No more false positives on wrong stacks.
- **JSONC skipping** — tsconfig.json, jsconfig.json, .vscode/ skipped by conftest-json
- **Extension-aware file length** — .py/.ts/.js: 500, .astro/.vue/.svelte: 800. Moved from Python-only to universal.
- **Biome VCS integration** — respects .gitignore via --vcs-enabled, skips dist/, .astro/, node_modules/
- **Dokploy stack** — auto-detection from `dokploy-network` in compose files, 2 Rego policies (traefik.enable required, dokploy-network required for Traefik-routed services)
- Tested on real JS project (iorlas.com Astro blog), 60 Python tests + 73 Rego tests

## Done (v0.2 — CLI simplification + monorepo)

- **CLI: 4 commands** — detect, init, lint, fix. Removed `audit` (absorbed by detect + init).
- **Monorepo support** — distributed dotfiles per subproject, `detect` scans subdirectories, `lint --all` / `fix --all` run all scopes in parallel via ThreadPoolExecutor
- **Makefile scaffolding** — `init` creates Makefile with `make lint` target, stack-appropriate test command
- **Init with tool reporting** — shows detected stacks + tool descriptions + availability (✓/✗), `--yes` for CI/agents
- **Workspace discovery** — `workspace.py` finds all `.agent-harness.yml` in the tree, skips excluded dirs
- 89 Python tests + 87 Rego tests

## Done (v0.3 — PyPI, conftest exceptions, multi-Dockerfile, skill redesign)

- **Published to PyPI** as `agentic-harness` (PEP 541 pending for `agent-harness` name)
- **GitHub Actions CI/CD** — CI on PRs, publish on tag push via trusted publishers
- **Git-aware file discovery** — `find_files` replaces hardcoded `SKIP_DIRS`, respects .gitignore
- **Multi-Dockerfile discovery** — Docker preset finds all Dockerfiles in tree, checks each with hadolint + conftest
- **Conftest exceptions** — 19 skippable policy IDs via `conftest_skip` in `.agent-harness.yml`
- **Project detection fix** — Docker-only directories no longer treated as subprojects
- **Init scaffold fix** — subprojects only get `.agent-harness.yml` + `.yamllint.yml`
- **Gitignore grouped append** — additions grouped by source template
- **Security audit** — osv-scanner + gitleaks, `security-audit` for working dir, `security-audit-history` for git history
- **Pre-commit hooks check** — lint verifies hooks are installed
- **SKILL.md redesign** — 3-phase product experience (Discover → Plan → Execute)
- **CONTRIBUTING.md** — uses agent-harness to develop agent-harness
- 44 Rego deny rules, 201 Python tests, 109 Rego tests

## Next (v0.4)

- **CLI init redesign** — richer narrative output matching the skill's 3-phase experience
- GitHub Actions workflow validation policies
- `.pre-commit-config.yaml` validation policies

## Future

- **Extensibility / custom presets** — enterprise teams bring their own policy bundles, custom presets, and tool configurations. Plugin system for adding stacks and rules without forking.
- Go stack module (golangci-lint, go test, go vet)
- `agent-harness upgrade` — pull latest policies without reinstalling
- Policy bundle versioning — pin and bump policy versions per project
- Config generation — `init` generates pyproject.toml ruff/coverage/pytest sections
- CLAUDE.md / AGENTS.md generation — `init` creates agent context file
- check-jsonschema integration (Compose schema, GitHub Actions schema validation)

## Non-goals

- **Embedding tools** (ruff, hadolint, conftest) — always external dependencies
- **Running in Docker** — must be <1s local execution
- **Replacing CI** — CI runs the same `agent-harness lint`, but local-first
- **Being a general-purpose linter** — this is specifically for AI agent harness engineering
