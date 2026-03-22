package gitignore.secrets

# GITIGNORE — secrets and artifacts must be excluded
#
# WHAT: Ensures .env, .venv, and __pycache__ are listed in .gitignore.
#
# WHY: Agents create .env files with real secrets during development and
# commit them. .venv and __pycache__ bloat the repo and slow git operations.
# Once secrets are in git history, they require history rewriting to remove.
#
# WITHOUT IT: Secrets in git history (extractable forever), 500MB repos from
# committed venvs, and slow clones on every CI run.
#
# FIX: Add .env, .venv, and __pycache__ to .gitignore.
#
# Input: array of [{Kind, Value, Original}] entries
# Parser: --parser ignore

import rego.v1

# Critical entries that must be in .gitignore
required_patterns := [".env", ".venv", "__pycache__"]

# ── Policy: critical patterns must be gitignored ──

deny contains msg if {
	some pattern in required_patterns
	not _pattern_present(pattern)
	msg := sprintf(".gitignore: '%s' is not ignored — agents may accidentally commit secrets or artifacts", [pattern])
}

_pattern_present(pattern) if {
	some entry in input
	entry.Kind == "Path"
	contains(entry.Value, pattern)
}
