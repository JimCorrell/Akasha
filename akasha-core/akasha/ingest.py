"""
Ebook ingestion pipeline: EPUB/PDF → Claude API → structured vault notes.

Produces one book index note and one note per chapter under Books/{Author} - {Title}/.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import anthropic

from .config import settings


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Chapter:
    number: int
    title: str
    text: str


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_epub(path: Path) -> tuple[str, str, list[Chapter]]:
    """Returns (title, author, chapters) from an EPUB file."""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(str(path), options={"ignore_ncx": True})

    title_meta = book.get_metadata("DC", "title")
    author_meta = book.get_metadata("DC", "creator")
    title = title_meta[0][0] if title_meta else path.stem
    author = author_meta[0][0] if author_meta else "Unknown"

    chapters = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")

        # Skip navigation documents
        if soup.find("nav") or soup.find(attrs={"epub:type": "toc"}):
            continue

        text = soup.get_text(separator="\n", strip=True)
        if len(text) < 300:
            continue

        heading = soup.find(["h1", "h2", "h3"])
        chapter_title = heading.get_text(strip=True) if heading else f"Section {len(chapters) + 1}"

        chapters.append(Chapter(
            number=len(chapters) + 1,
            title=chapter_title,
            text=text,
        ))

    return title, author, chapters


def extract_pdf(path: Path) -> tuple[str, str, list[Chapter]]:
    """Returns (title, author, chapters) from a PDF file."""
    import fitz  # pymupdf

    doc = fitz.open(str(path))
    meta = doc.metadata
    title = meta.get("title") or path.stem
    author = meta.get("author") or "Unknown"

    toc = doc.get_toc()
    top_level = [(t, p) for lvl, t, p in toc if lvl == 1]

    if not top_level:
        # Try level 2 if no level-1 entries
        top_level = [(t, p) for lvl, t, p in toc if lvl <= 2]

    if top_level:
        chapters = _pdf_by_toc(doc, top_level)
    else:
        chapters = _pdf_by_page_chunks(doc)

    return title, author, chapters


def _pdf_by_toc(doc, toc_entries: list[tuple[str, int]]) -> list[Chapter]:
    chapters = []
    for i, (ch_title, start_page) in enumerate(toc_entries):
        end_page = toc_entries[i + 1][1] if i + 1 < len(toc_entries) else len(doc) + 1
        text = "\n".join(
            doc[p].get_text()
            for p in range(max(0, start_page - 1), min(end_page - 1, len(doc)))
        ).strip()
        if len(text) < 300:
            continue
        chapters.append(Chapter(number=len(chapters) + 1, title=ch_title, text=text))
    return chapters


def _pdf_by_page_chunks(doc, pages_per_chunk: int = 25) -> list[Chapter]:
    chapters = []
    for start in range(0, len(doc), pages_per_chunk):
        end = min(start + pages_per_chunk, len(doc))
        text = "\n".join(doc[p].get_text() for p in range(start, end)).strip()
        if len(text) < 300:
            continue
        chapters.append(Chapter(
            number=len(chapters) + 1,
            title=f"Pages {start + 1}–{end}",
            text=text,
        ))
    return chapters


# ---------------------------------------------------------------------------
# Claude extraction — tool use guarantees valid structured output
# ---------------------------------------------------------------------------

_CHAPTER_TOOL = {
    "name": "save_chapter_knowledge",
    "description": "Save extracted knowledge from a book chapter into a personal knowledge base.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "2-4 paragraphs capturing the main ideas and arguments",
            },
            "key_concepts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "5-10 key concepts or ideas from the chapter",
            },
            "quotes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Up to 5 notable quotes worth remembering",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-6 lowercase hyphenated descriptive tags",
            },
        },
        "required": ["summary", "key_concepts", "quotes", "tags"],
    },
}

_BOOK_TOOL = {
    "name": "save_book_overview",
    "description": "Save a structured overview of a book into a personal knowledge base.",
    "input_schema": {
        "type": "object",
        "properties": {
            "overview": {
                "type": "string",
                "description": "2-3 paragraphs summarizing the book's main ideas and value",
            },
            "key_themes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "5-8 overarching themes across the book",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "5-10 lowercase hyphenated tags for the whole book",
            },
        },
        "required": ["overview", "key_themes", "tags"],
    },
}

_CHAPTER_PROMPT = """\
You are extracting key knowledge from a book chapter for a personal knowledge base.

Book: "{title}" by {author}
Chapter {number}: "{chapter_title}"

---
{text}
---

Extract and save the key knowledge from this chapter.\
"""

_BOOK_PROMPT = """\
You are creating an overview for a book in a personal knowledge base.

Book: "{title}" by {author}

Chapter summaries:
{summaries}

Save a structured overview of the whole book.\
"""


def _call_claude_tool(client: anthropic.Anthropic, tool: dict, prompt: str) -> dict:
    msg = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError("Claude did not return a tool_use block")


def process_chapter(client: anthropic.Anthropic, title: str, author: str, chapter: Chapter) -> dict:
    prompt = _CHAPTER_PROMPT.format(
        title=title,
        author=author,
        number=chapter.number,
        chapter_title=chapter.title,
        text=chapter.text[:40_000],
    )
    return _call_claude_tool(client, _CHAPTER_TOOL, prompt)


def process_book_overview(client: anthropic.Anthropic, title: str, author: str,
                           chapter_results: list[dict]) -> dict:
    summaries = "\n\n".join(
        f"Chapter {i + 1}: {r.get('summary', '')[:600]}"
        for i, r in enumerate(chapter_results)
    )
    prompt = _BOOK_PROMPT.format(
        title=title,
        author=author,
        summaries=summaries[:30_000],
    )
    return _call_claude_tool(client, _BOOK_TOOL, prompt)


# ---------------------------------------------------------------------------
# Note writing
# ---------------------------------------------------------------------------

def _slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip()
    text = re.sub(r"[-\s]+", " ", text)
    return text[:max_len].strip()


def _clean_chapter_title(title: str) -> str:
    """Strip leading chapter/part number prefixes that duplicate the note number.

    Handles patterns like:
      "Chapter 1: Foo"  → "Foo"
      "Chapter 1 - Foo" → "Foo"
      "1. Foo"          → "Foo"
      "1 - Foo"         → "Foo"
      "CHAPTER ONE Foo" → "Foo"
    """
    # "Chapter N: title", "Chapter N - title", "Chapter N. title", "Chapter N title"
    title = re.sub(
        r"^chapter\s+[\w]+[\s:.\-–—]+",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    # "Part N: title" — keep "Part N" as context, just strip the delimiter
    title = re.sub(r"^(part\s+[\w]+)\s*[:\-–—]\s*", r"\1 - ", title, flags=re.IGNORECASE)
    # Leading "N. title" or "N - title" or "N: title"
    title = re.sub(r"^\d+\s*[.:\-–—]\s*", "", title).strip()
    return title or title  # return original if everything got stripped


def _yaml_tags(tags: list[str]) -> str:
    return "\n".join(f"  - {t}" for t in tags)


def write_chapter_note(vault_path: Path, book_dir_name: str, title: str, author: str,
                        chapter: Chapter, extracted: dict) -> Path:
    note_dir = vault_path / "Books" / book_dir_name
    note_dir.mkdir(parents=True, exist_ok=True)

    clean_title = _clean_chapter_title(chapter.title)
    filename = f"{chapter.number:02d} - {_slugify(clean_title)}.md"
    note_path = note_dir / filename

    tags = extracted.get("tags", [])
    concepts = "\n".join(f"- {c}" for c in extracted.get("key_concepts", []))
    quotes = "\n\n".join(f'> "{q}"' for q in extracted.get("quotes", []))

    note_path.write_text(f"""\
---
type: book-chapter
book: "{title}"
author: "{author}"
chapter: {chapter.number}
chapter_title: "{chapter.title}"
tags:
{_yaml_tags(tags)}
---
# {chapter.number}. {clean_title}

## Summary
{extracted.get("summary", "")}

## Key Concepts
{concepts}

## Notable Quotes
{quotes if quotes else "_None extracted._"}

## My Notes
<!-- Add your own thoughts here -->
""", encoding="utf-8")

    return note_path


def write_book_note(vault_path: Path, book_dir_name: str, title: str, author: str,
                     overview: dict, chapter_filenames: list[str]) -> Path:
    note_dir = vault_path / "Books" / book_dir_name
    note_dir.mkdir(parents=True, exist_ok=True)

    note_path = note_dir / f"{_slugify(title)}.md"

    tags = overview.get("tags", [])
    themes = "\n".join(f"- {t}" for t in overview.get("key_themes", []))
    # Wikilinks use filename without extension
    chapter_links = "\n".join(
        f"- [[{Path(f).stem}]]" for f in chapter_filenames
    )

    note_path.write_text(f"""\
---
type: book
title: "{title}"
author: "{author}"
chapters: {len(chapter_filenames)}
tags:
{_yaml_tags(tags)}
---
# {title}
**Author**: {author}

## Overview
{overview.get("overview", "")}

## Key Themes
{themes}

## Chapters
{chapter_links}
""", encoding="utf-8")

    return note_path


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def ingest(path: Path, vault_path: Path | None = None, on_progress=None) -> Path:
    """
    Ingest an ebook into the vault. Returns the path of the book index note.
    on_progress(message: str) is called after each chapter is written.
    """
    vault = vault_path or settings.vault_path
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Extract text
    suffix = path.suffix.lower()
    if suffix == ".epub":
        title, author, chapters = extract_epub(path)
    elif suffix == ".pdf":
        title, author, chapters = extract_pdf(path)
    else:
        raise ValueError(f"Unsupported format: {suffix}. Use .epub or .pdf")

    if not chapters:
        raise ValueError("No content extracted from file.")

    book_dir_name = _slugify(title)

    # Process each chapter
    chapter_results = []
    chapter_filenames = []

    for chapter in chapters:
        extracted = process_chapter(client, title, author, chapter)
        note_path = write_chapter_note(vault, book_dir_name, title, author, chapter, extracted)
        chapter_results.append(extracted)
        chapter_filenames.append(note_path.name)
        if on_progress:
            on_progress(f"Chapter {chapter.number}: {chapter.title}")

    # Write book index
    overview = process_book_overview(client, title, author, chapter_results)
    book_note = write_book_note(vault, book_dir_name, title, author, overview, chapter_filenames)

    return book_note
