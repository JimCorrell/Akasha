"""Tests for pure indexer functions — no filesystem or embedding calls needed."""

import pytest

from akasha.indexer import _build_embed_text, _clean_body
from akasha.ingest import _clean_chapter_title


class TestCleanBody:
    def test_strips_wikilinks(self):
        body = "See [[Some Note]] for details."
        assert "[[" not in _clean_body(body)
        assert "Some Note" in _clean_body(body)

    def test_strips_markdown_links(self):
        body = "Read [this article](https://example.com) now."
        assert "https://example.com" not in _clean_body(body)
        assert "this article" in _clean_body(body)

    def test_strips_list_bullets(self):
        body = "- First item\n- Second item\n* Third"
        result = _clean_body(body)
        assert "- " not in result
        assert "First item" in result

    def test_collapses_blank_lines(self):
        body = "Line one\n\n\n\nLine two"
        assert "\n\n\n" not in _clean_body(body)

    def test_empty_string(self):
        assert _clean_body("") == ""


class TestBuildEmbedText:
    def test_book_chapter_extracts_sections(self):
        body = """\
## Summary
This chapter covers leadership.

## Key Takeaways
- Be decisive
- Communicate clearly

## Frameworks & Models
- RACI matrix: assigns roles

## Notable Quotes
> "Lead by example."

## My Notes
<!-- Add your thoughts here -->
"""
        result = _build_embed_text("Chapter 1", body, "book-chapter")
        assert "This chapter covers leadership" in result
        assert "Be decisive" in result
        assert "RACI matrix" in result
        # Should NOT include the My Notes placeholder
        assert "Add your thoughts" not in result

    def test_book_chapter_falls_back_to_full_body_when_no_sections(self):
        body = "Just some plain text with no markdown headings."
        result = _build_embed_text("My Chapter", body, "book-chapter")
        assert "Just some plain text" in result

    def test_non_book_chapter_uses_full_body(self):
        body = "## Summary\nSome summary.\n\n## Other\nOther stuff."
        result = _build_embed_text("My Note", body, "note")
        assert "Other stuff" in result

    def test_title_always_included(self):
        body = "Some content here."
        result = _build_embed_text("Important Title", body, "book-chapter")
        assert "Important Title" in result


class TestCleanChapterTitle:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("Chapter 1: Managing Up", "Managing Up"),
            ("Chapter 1 - Managing Up", "Managing Up"),
            ("chapter one Managing Up", "Managing Up"),
            ("1. Managing Up", "Managing Up"),
            ("1 - Managing Up", "Managing Up"),
            ("1 Managing Up", "Managing Up"),
            ("appendix Managing Up", "Managing Up"),
            ("Managing Up", "Managing Up"),  # already clean
        ],
    )
    def test_strips_prefixes(self, raw, expected):
        assert _clean_chapter_title(raw) == expected
