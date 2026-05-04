#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Akasha Search
# @raycast.mode fullOutput
# @raycast.packageName Akasha

# Optional parameters:
# @raycast.icon 🔮
# @raycast.argument1 { "type": "text", "placeholder": "Search your notes..." }
# @raycast.description Semantic search across your personal knowledge base

import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

AKASHA_CORE = "/Users/jimcorrell/development/neho software/Akasha/akasha-core"
OBSIDIAN_VAULT = "akasha"
API = "http://localhost:8765"
POETRY = "/opt/homebrew/bin/poetry"


def server_running() -> bool:
    try:
        urllib.request.urlopen(f"{API}/health", timeout=2)
        return True
    except Exception:
        return False


def start_server():
    print("Starting Akasha server...")
    subprocess.Popen(
        [POETRY, "run", "akasha-serve"],
        cwd=AKASHA_CORE,
        stdout=open("/tmp/akasha.log", "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(10):
        time.sleep(0.5)
        if server_running():
            print("Server ready.\n")
            return
    print("Could not start Akasha server. Check /tmp/akasha.log for details.")
    sys.exit(1)


def search(query: str, limit: int = 5) -> dict:
    payload = json.dumps({"query": query, "limit": limit}).encode()
    req = urllib.request.Request(
        f"{API}/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    if not query.strip():
        print("Enter a search query.")
        return

    if not server_running():
        start_server()

    data = search(query)
    results = data["results"]

    if not results:
        print("No results found.")
        return

    n = len(results)
    ms = data["query_time_ms"]
    total = data["total_notes"]
    print(f"🔮  {n} result{'s' if n != 1 else ''}  ·  {ms}ms  ·  {total} notes indexed\n")

    for i, r in enumerate(results, 1):
        score = r["score"]
        bar = "█" * round(score * 8) + "░" * (8 - round(score * 8))
        tags = ("  " + "  ".join(f"#{t}" for t in r["tags"])) if r["tags"] else ""
        encoded = urllib.parse.quote(r["path"], safe="/")
        url = f"obsidian://open?vault={OBSIDIAN_VAULT}&file={encoded}"

        print(f"{i}.  {r['title']}{tags}")
        if r["snippet"]:
            s = r["snippet"]
            print(f"    {s[:120]}{'…' if len(s) > 120 else ''}")
        print(f"    [{bar}] {score:.2f}  ·  {url}")
        print()


if __name__ == "__main__":
    main()
