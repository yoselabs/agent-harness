from __future__ import annotations
import subprocess
import shutil
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    output: str = ""
    error: str = ""
    duration_ms: int = 0


def tool_available(tool: str, project_dir: Path) -> bool:
    """Check if a tool is available — globally, in .venv, or in node_modules."""
    if shutil.which(tool):
        return True
    venv_bin = project_dir / ".venv" / "bin" / tool
    if venv_bin.exists():
        return True
    node_bin = project_dir / "node_modules" / ".bin" / tool
    if node_bin.exists():
        return True
    return False


def _resolve_tool(tool: str, cwd: str | None = None) -> str | None:
    """Find a tool binary — PATH first, then .venv/bin, then node_modules/.bin."""
    found = shutil.which(tool)
    if found:
        return found
    if cwd:
        project_dir = Path(cwd)
        venv_bin = project_dir / ".venv" / "bin" / tool
        if venv_bin.exists():
            return str(venv_bin)
        node_bin = project_dir / "node_modules" / ".bin" / tool
        if node_bin.exists():
            return str(node_bin)
    return None


def run_check(name: str, cmd: list[str], cwd: str | None = None) -> CheckResult:
    """Run a check command and return structured result."""
    tool = cmd[0]
    resolved = _resolve_tool(tool, cwd)
    if not resolved:
        return CheckResult(
            name=name,
            passed=False,
            error=f"{tool} not found — not installed or not in PATH",
        )
    # Use resolved path for the tool binary
    cmd = [resolved] + cmd[1:]
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=60
        )
        duration = int((time.monotonic() - start) * 1000)
        return CheckResult(
            name=name,
            passed=result.returncode == 0,
            output=result.stdout,
            error=result.stderr,
            duration_ms=duration,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(name=name, passed=False, error=f"{name} timed out after 60s")
