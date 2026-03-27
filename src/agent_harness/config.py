"""Config loading — dict-based, each preset reads its own section."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


def _resolve_git_root(project_dir: Path) -> Path | None:
    """Find the git repository root for project_dir, or None if not in a repo."""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        cwd=str(project_dir),
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def load_config(project_dir: Path) -> dict:
    """Load .agent-harness.yml. Returns dict."""
    config: dict = {"stacks": set(), "exclude": []}
    config["git_root"] = _resolve_git_root(project_dir)
    cfg_path = project_dir / ".agent-harness.yml"

    if cfg_path.exists():
        try:
            raw = yaml.safe_load(cfg_path.read_text()) or {}
        except yaml.YAMLError as e:
            import click

            click.echo(
                f"  WARNING: {cfg_path} is malformed, using defaults\n  {e}", err=True
            )
            raw = {}

        if "stacks" in raw:
            config["stacks"] = set(raw["stacks"])
        if "exclude" in raw:
            config["exclude"] = list(raw["exclude"])

        # Pass through all other sections for presets to read
        for key, value in raw.items():
            if key not in ("stacks", "exclude"):
                config[key] = value

    # Auto-detect if no stacks specified
    if not config["stacks"]:
        from agent_harness.registry import PRESETS

        config["stacks"] = {p.name for p in PRESETS if p.detect(project_dir)}

    return config
