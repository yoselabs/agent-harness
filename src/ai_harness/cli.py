# src/ai_harness/cli.py
import click
from pathlib import Path

@click.group()
@click.version_option()
def cli():
    """AI Harness — deterministic controls for AI agents."""

@cli.command()
def detect():
    """Detect project stacks (Python, Docker, etc.)."""
    from ai_harness.detect import detect_stacks
    stacks = detect_stacks(Path.cwd())
    if stacks:
        for stack in sorted(stacks):
            click.echo(stack)
    else:
        click.echo("no stacks detected")

@cli.command()
def lint():
    """Run all harness checks."""
    click.echo("lint: not implemented")

@cli.command()
def fix():
    """Auto-fix what's fixable, then lint."""
    click.echo("fix: not implemented")

@cli.command()
def init():
    """Initialize harness on a project."""
    click.echo("init: not implemented")

@cli.command()
def audit():
    """Audit harness configuration completeness."""
    click.echo("audit: not implemented")
