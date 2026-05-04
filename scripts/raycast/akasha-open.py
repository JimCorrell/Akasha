#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Akasha Open Note
# @raycast.mode silent
# @raycast.packageName Akasha

# Optional parameters:
# @raycast.icon 📝
# @raycast.argument1 { "type": "text", "placeholder": "vault-relative path, e.g. People/Jay Johnson.md" }
# @raycast.description Open a note in Obsidian by its vault-relative path

import subprocess
import sys
import urllib.parse

OBSIDIAN_VAULT = "akasha"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    if not path.strip():
        print("Enter a vault-relative file path.")
        return

    encoded = urllib.parse.quote(path, safe="/")
    url = f"obsidian://open?vault={OBSIDIAN_VAULT}&file={encoded}"
    subprocess.run(["open", url])


if __name__ == "__main__":
    main()
