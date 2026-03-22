from pathlib import Path
from ai_harness.runner import run_check, CheckResult
import shutil


def run_ty(project_dir: Path) -> CheckResult:
    """Run ty type checker. Falls back to uv run ty if ty not in PATH."""
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.exists():
        return CheckResult(name="ty", passed=True, output="No pyproject.toml, skipping")
    if shutil.which("ty"):
        return run_check("ty", ["ty", "check"], cwd=str(project_dir))
    return run_check("ty", ["uv", "run", "ty", "check"], cwd=str(project_dir))
