.PHONY: lint fix test

lint:
	agent-harness lint

fix:
	agent-harness fix

test:
	uv run pytest tests/ -v
	conftest verify -p src/agent_harness/policies/ --no-color
