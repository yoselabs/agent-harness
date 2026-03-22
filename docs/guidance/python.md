# Python Guidance

Non-deterministic guidance for Python stack — reasoning behind config choices that can't be expressed as Rego policies.

Deterministic configs (ruff, ty, pytest, coverage, CI workflow, Dockerfile template) live in `src/agent_harness/stacks/python/templates.py`. Use `agent-harness audit` and `agent-harness init` for config generation and gap analysis.

---

## Why Each Knob Matters for AI

These are the reasoning notes for config choices — the templates have the values, this explains the judgment:

- `output-format = "concise"` — agent sees `file.py:42:5 E501 Line too long`, not a 5-line context block. The #1 knob for agent readability.
- `line-length = 140` — modern screens; avoids agents reformatting lines that are fine
- `extend-exclude` — agents shouldn't lint generated code; without this they'll try to "fix" it
- `per-file-ignores` for tests — generous: agents shouldn't fight the test framework
- `T20` (no print) — catches leftover `print()` debug statements agents forget to remove
- `G` + `LOG` — prevents `log.info(f"...")` which agents default to; structured fields are searchable
- `BLE` — catches bare `except:` which agents sometimes generate
- `TC` — moves type-only imports behind `TYPE_CHECKING`, reducing runtime import cost
- `C90` — agents generate deeply nested functions when not constrained; complexity limit forces decomposition
- `term:skip-covered` — with 95% coverage, most files are green. Without this, agent sees 50+ green files drowning 2 that need work
- `show_missing = false` — missing line numbers add noise; XML report has them for diff-cover
- Optional: `--tb=short` — for large test suites, reduces traceback flood

---

## Common Mistakes (Python)

- Adding harness config without `output-format = "concise"` — the #1 knob for agent readability
- Blindly applying `A002`/`A003` renames in API-facing code — renaming `id` to `torrent_id` in an MCP tool changes the schema. Projects with APIs: add "Ask First: before renaming function parameters in API-facing code" to agent context file
- Writing guidelines for humans — "here are your options" vs "do X, because Y"
