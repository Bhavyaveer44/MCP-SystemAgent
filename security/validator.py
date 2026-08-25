import re
import shlex
from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "allowed_commands.yaml"


class CommandRejected(Exception):
    pass


class CommandValidator:
    def __init__(self, config_path: Path = CONFIG_PATH):
        with open(config_path) as f:
            self._rules = yaml.safe_load(f)["commands"]

    def validate(self, raw_command: str) -> dict:
        """
        Parses a shell command string and checks it against the allowlist.
        Returns a dict describing the command, or raises CommandRejected.
        """
        parts = shlex.split(raw_command)
        if not parts:
            raise CommandRejected("Empty command")

        binary, args = parts[0], parts[1:]
        rule = self._rules.get(binary)
        if rule is None:
            raise CommandRejected(f"'{binary}' is not on the allowlist")

        arg_string = " ".join(args)
        if not re.fullmatch(rule["pattern"], arg_string):
            raise CommandRejected(
                f"'{binary} {arg_string}' does not match the allowed pattern for '{binary}'"
            )

        needs_confirmation = any(
            re.fullmatch(pat, args[0] if args else "", ) or pat == ".*"
            for pat in rule.get("requires_confirmation", [])
        )

        return {
            "binary": binary,
            "args": args,
            "full_command": raw_command,
            "needs_confirmation": needs_confirmation,
        }