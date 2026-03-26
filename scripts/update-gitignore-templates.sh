#!/usr/bin/env bash
# Fetch latest gitignore templates from github/gitignore.
# Run manually when templates need updating.
set -euo pipefail

DEST="src/agent_harness/templates/gitignore"
BASE="https://raw.githubusercontent.com/github/gitignore/main"

mkdir -p "$DEST"

echo "Fetching language templates..."
curl -sf "$BASE/Python.gitignore" -o "$DEST/Python.gitignore"
curl -sf "$BASE/Node.gitignore" -o "$DEST/Node.gitignore"

echo "Fetching OS globals..."
curl -sf "$BASE/Global/macOS.gitignore" -o "$DEST/macOS.gitignore"
curl -sf "$BASE/Global/Windows.gitignore" -o "$DEST/Windows.gitignore"
curl -sf "$BASE/Global/Linux.gitignore" -o "$DEST/Linux.gitignore"

echo "Done. Review changes with: git diff $DEST/"
