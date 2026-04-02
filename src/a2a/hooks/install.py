"""Install/uninstall the PostToolUse hook into .claude/settings.json."""
import json
import os
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "post_bash.sh"

HOOK_ENTRY = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": f"bash {HOOK_SCRIPT.resolve()}",
            "timeout": 10,
        }
    ],
}


def install(settings_path: str | None = None):
    """Add the PostToolUse hook to the given settings.json."""
    if settings_path is None:
        settings_path = os.path.expanduser("~/.claude/settings.json")

    path = Path(settings_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        settings = json.loads(path.read_text())
    else:
        settings = {}

    post_hooks = settings.setdefault("PostToolUse", [])

    # Check if our hook is already installed (by script path)
    script_str = str(HOOK_SCRIPT.resolve())
    for entry in post_hooks:
        for hook in entry.get("hooks", []):
            if script_str in hook.get("command", ""):
                return  # already installed

    post_hooks.append(HOOK_ENTRY)
    path.write_text(json.dumps(settings, indent=2) + "\n")


def uninstall(settings_path: str | None = None):
    """Remove the PostToolUse hook from the given settings.json."""
    if settings_path is None:
        settings_path = os.path.expanduser("~/.claude/settings.json")

    path = Path(settings_path)
    if not path.exists():
        return

    settings = json.loads(path.read_text())
    post_hooks = settings.get("PostToolUse", [])

    script_str = str(HOOK_SCRIPT.resolve())
    settings["PostToolUse"] = [
        entry for entry in post_hooks
        if not any(script_str in h.get("command", "") for h in entry.get("hooks", []))
    ]

    if not settings["PostToolUse"]:
        del settings["PostToolUse"]

    path.write_text(json.dumps(settings, indent=2) + "\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
        print("Hook uninstalled.")
    else:
        install()
        print("Hook installed.")
