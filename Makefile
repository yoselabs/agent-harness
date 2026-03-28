.PHONY: lint fix test check security-audit bootstrap

lint:
	agent-harness lint

fix:
	agent-harness fix

test:
	uv run pytest tests/ -v
	conftest verify -p src/agent_harness/policies/ --no-color

security-audit:
	agent-harness security-audit

check: lint test security-audit

bootstrap: ## First-time setup after clone
	uv sync
	agent-harness init --apply
	@if command -v prek >/dev/null; then prek install; \
	elif command -v pre-commit >/dev/null; then pre-commit install; \
	else echo "Install prek (brew install prek) or pre-commit for git hooks"; fi
	@echo "Done. Run 'make check' to verify."
