import subprocess
from pathlib import Path

from security.validator import CommandValidator, CommandRejected

WORKSPACE = (Path(__file__).parent.parent / "workspace").resolve()
validator = CommandValidator()


def run_command(raw_command: str, approved: bool = False) -> str:
    try:
        info = validator.validate(raw_command)
    except CommandRejected as e:
        return f"REJECTED: {e}"

    if info["needs_confirmation"] and not approved:
        return f"CONFIRMATION_REQUIRED: {raw_command}"

    try:
        result = subprocess.run(
            [info["binary"], *info["args"]],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 30s"

    output = result.stdout
    if result.returncode != 0:
        output += f"\n[stderr] {result.stderr}\n[exit code: {result.returncode}]"
    return output