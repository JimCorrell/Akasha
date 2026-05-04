import hashlib
import re
from datetime import datetime
from pathlib import Path

import frontmatter

from .config import settings
from . import embeddings, store


def _parse_note(path: Path) -> dict:
    post = frontmatter.load(str(path))
    body: str = post.content
    meta: dict = post.metadata

    title = meta.get("title") or _first_heading(body) or path.stem
    tags = meta.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    return {
        "title": str(title),
        "path": str(path.relative_to(settings.vault_path)),
        "tags": [str(t) for t in tags],
        "snippet": _extract_snippet(body),
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "type": str(meta.get("type", "")),
        "embed_text": f"{title}\n\n{body}",
        "content_hash": hashlib.md5(path.read_bytes()).hexdigest(),
    }


def _first_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _extract_snippet(body: str, max_len: int = 200) -> str:
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("---"):
            continue
        # strip wikilinks and markdown links
        line = re.sub(r"\[\[([^\]]+)\]\]", r"\1", line)
        line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
        line = line.strip()
        if line:
            return line[:max_len]
    return ""


def note_id(path: Path) -> str:
    return str(path.relative_to(settings.vault_path))


def _is_hidden(path: Path) -> bool:
    return any(part.startswith(".") for part in path.relative_to(settings.vault_path).parts)


def index_note(path: Path) -> bool:
    try:
        note = _parse_note(path)
        metadata = {
            "title": note["title"],
            "path": note["path"],
            "tags": ",".join(note["tags"]),
            "modified": note["modified"],
            "type": note["type"],
            "content_hash": note["content_hash"],
        }
        embedding = embeddings.embed(note["embed_text"])
        store.upsert(note_id(path), embedding, metadata, note["snippet"])
        return True
    except Exception as e:
        print(f"  Error indexing {path.name}: {e}")
        return False


def remove_note(path: Path):
    store.delete(note_id(path))


def index_vault(vault_path: Path | None = None, force: bool = False) -> tuple[int, int]:
    """Scan all markdown files and index new or changed ones. Returns (indexed, skipped)."""
    vault = vault_path or settings.vault_path
    md_files = [p for p in vault.rglob("*.md") if not _is_hidden(p)]

    # Build map of existing content hashes for change detection
    existing: dict[str, str] = {}
    if not force:
        try:
            col = store._get_collection()
            if col.count() > 0:
                result = col.get(include=["metadatas"])
                for meta in result["metadatas"]:
                    existing[meta.get("path", "")] = meta.get("content_hash", "")
        except Exception:
            pass

    indexed = skipped = 0
    for path in md_files:
        rel = str(path.relative_to(vault))
        current_hash = hashlib.md5(path.read_bytes()).hexdigest()
        if not force and existing.get(rel) == current_hash:
            skipped += 1
            continue
        print(f"  Indexing: {rel}")
        if index_note(path):
            indexed += 1

    return indexed, skipped
