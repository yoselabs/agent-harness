import click
from pathlib import Path

from agent_harness.detect import detect_stacks
from agent_harness.init.templates import (
    HARNESS_YML,
    YAMLLINT_YML,
    PRECOMMIT_YML,
    MAKEFILE,
)
from agent_harness.registry import PRESETS
from agent_harness.runner import tool_available
from agent_harness.presets.javascript.templates import BIOME_CONFIG


def scaffold_project(project_dir: Path, yes: bool = False) -> list[str]:
    """Write harness config files. Returns list of actions taken."""
    stacks = detect_stacks(project_dir)
    stacks_str = ", ".join(sorted(stacks)) if stacks else "none detected"
    stacks_list = ", ".join(sorted(stacks))

    # Show what was detected
    click.echo(f"  Detected stacks: {stacks_str}")
    click.echo()

    for preset in PRESETS:
        if preset.name in stacks:
            info = preset.get_info()
            click.echo(f"  {info.name}:")
            for tool in info.tools:
                available = tool_available(tool.binary, project_dir)
                status = (
                    "\u2713 installed"
                    if available
                    else f"\u2717 not found ({tool.install_hint})"
                )
                click.echo(
                    f"    {tool.name:<14} \u2014 {tool.description:<30} {status}"
                )
            click.echo()

    # Confirmation
    if not yes:
        if not click.confirm("  Proceed?", default=True):
            return ["Cancelled"]

    # Determine test command for Makefile
    if "python" in stacks:
        test_command = "uv run pytest tests/ -v"
    elif "javascript" in stacks:
        test_command = "npm test"
    else:
        test_command = 'echo "no test command configured"'

    actions = []
    files: dict[str, str] = {
        ".agent-harness.yml": HARNESS_YML.format(
            stacks=stacks_str, stacks_list=stacks_list
        ),
        ".yamllint.yml": YAMLLINT_YML,
        ".pre-commit-config.yaml": PRECOMMIT_YML,
        "Makefile": MAKEFILE.format(test_command=test_command),
    }

    # JS stack: scaffold biome.json
    if "javascript" in stacks:
        files["biome.json"] = BIOME_CONFIG

    for filename, content in files.items():
        path = project_dir / filename
        if path.exists():
            actions.append(f"SKIP  {filename} (already exists)")
        else:
            path.write_text(content)
            actions.append(f"CREATE  {filename}")

    return actions
