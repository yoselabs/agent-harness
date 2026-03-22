# Refactor: Stack Separation + Rename

> **For agentic workers:** Use superpowers:subagent-driven-development to implement.

**Goal:** Rename ai_harness → agent_harness, restructure checks into per-stack directories with one check per file, one test per check.

**Why:** Adding Ruby/Go/JS later should be "create a new stacks/ directory" not "edit 5 existing files." Each check is a self-contained unit with its own test.

## Current structure (flat)
```
src/ai_harness/checks/conftest.py     # 5 functions mixed
src/ai_harness/checks/ruff.py
src/ai_harness/checks/ty.py
src/ai_harness/checks/hadolint.py
src/ai_harness/checks/yamllint_check.py
src/ai_harness/checks/file_length.py
```

## Target structure (per-stack, one file per check)
```
src/agent_harness/
  cli.py, config.py, runner.py, lint.py, fix.py, audit.py
  stacks/
    python/
      detect.py, ruff_check.py, ty_check.py, file_length_check.py, 
      conftest_python.py, templates.py
    docker/
      detect.py, hadolint_check.py, conftest_dockerfile.py,
      conftest_compose.py, templates.py
    universal/
      yamllint_check.py, conftest_json.py, conftest_gitignore.py,
      templates.py

tests/
  stacks/python/test_ruff_check.py, test_ty_check.py, ...
  stacks/docker/test_hadolint_check.py, ...
  stacks/universal/test_yamllint_check.py, ...
  fixtures/dockerfile/, fixtures/compose/
  test_cli.py, test_config.py, test_detect.py, test_runner.py
```

## Convention: every check file is self-documented

Same pattern as Rego policies. Every check file has a module docstring:

```python
"""
<Check name>.

WHAT: <One sentence — what this check does>

WHY: <2-3 sentences — why AI agents need this specific check>

WITHOUT IT: <Concrete failure scenario>

FIX: <How to resolve — exact command or action>

REQUIRES: <External tool(s) needed>
"""
```

The file IS the documentation. An agent reading the file understands everything — no external docs needed. When a user challenges a check, the agent reads the docstring and cites the WHY.

## Tasks
1. Rename ai_harness → agent_harness (module name, imports, pyproject.toml)
2. Create stacks/ directory structure
3. Move checks into per-stack directories (one file per check, with WHAT/WHY/WITHOUT IT/FIX docstrings)
4. Move tests to mirror structure (one test file per check file)
5. Update lint.py to discover checks from stacks/
6. Update all imports
7. Move config templates from K skill's python.md/docker.md into per-stack templates.py
8. Verify all tests pass
9. Test on aggre
10. Strip K skill's python.md and docker.md to guidance-only (non-deterministic advice)
