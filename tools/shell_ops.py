import subprocess
from pathlib import Path

from security.validator import CommandValidator, CommandRejected

WORKSPACE = (Path(__file__).parent.parent / "workspace").resolve()
validator = CommandValidator()


class CommandDenied(Exception):
    """Raised when the user declines a confirmation prompt."""
    pass


def _confirm(command_info: dict) -> bool:
    print("\n--- CONFIRMATION REQUIRED ---")
    print(f"Command: {command_info['full_command']}")
    print(f"Running in: {WORKSPACE}")
    answer = input("Allow this command? [y/N]: ").strip().lower()
    return answer == "y"


def run_command(raw_command: str) -> str:
    """
    Validates a shell command against the allowlist, asks for local
    user confirmation if required, then executes it inside WORKSPACE.
    """
    try:
        command_info = validator.validate(raw_command)
    except CommandRejected as e:
        return f"REJECTED: {e}"

    if command_info["needs_confirmation"]:
        if not _confirm(command_info):
            raise CommandDenied(f"User declined: {raw_command}")

    result = subprocess.run(
        [command_info["binary"], *command_info["args"]],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout
    if result.returncode != 0:
        output += f"\n[stderr] {result.stderr}\n[exit code: {result.returncode}]"

    return output