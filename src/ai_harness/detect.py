from pathlib import Path

STACK_INDICATORS = {
    "python": ["pyproject.toml", "setup.py", "requirements.txt", "uv.lock"],
    "docker": ["Dockerfile", "docker-compose.prod.yml", "docker-compose.yml"],
}


def detect_stacks(project_dir: Path) -> set[str]:
    """Detect which stacks a project uses based on file presence."""
    stacks = set()
    for stack, indicators in STACK_INDICATORS.items():
        for indicator in indicators:
            if (project_dir / indicator).exists():
                stacks.add(stack)
                break
    return stacks
