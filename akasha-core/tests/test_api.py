"""Tests for API endpoints using FastAPI's TestClient with mocked dependencies."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from akasha.main import app

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def mock_watcher():
    """Prevent the vault watcher from starting during tests."""
    mock_observer = MagicMock()
    with patch("akasha.watcher.start_watcher", return_value=mock_observer):
        yield


class TestHealth:
    def test_returns_ok(self):
        with patch("akasha.store.count", return_value=42):
            res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["notes"] == 42


class TestSearch:
    def test_empty_query_returns_400(self):
        res = client.post("/search", json={"query": "  "})
        assert res.status_code == 400

    def test_valid_query_returns_results(self):
        fake_embedding = [0.1] * 384
        fake_results = [
            {
                "score": 0.85,
                "metadata": {
                    "title": "Test Note",
                    "path": "Books/Test/01 - Intro.md",
                    "tags": "leadership,management",
                    "modified": "2024-01-01T00:00:00",
                    "type": "book-chapter",
                },
                "snippet": "Leadership is about empowering others to make decisions.",
            }
        ]
        with (
            patch("akasha.embeddings.embed", return_value=fake_embedding),
            patch("akasha.store.search", return_value=fake_results),
            patch("akasha.store.count", return_value=10),
        ):
            res = client.post("/search", json={"query": "leadership"})

        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Test Note"
        assert data["results"][0]["score"] == 0.85
        assert data["total_notes"] == 10

    def test_tags_parsed_correctly(self):
        fake_embedding = [0.0] * 384
        fake_results = [
            {
                "score": 0.7,
                "metadata": {
                    "title": "Tagged Note",
                    "path": "note.md",
                    "tags": "foo,bar,baz",
                    "modified": None,
                    "type": "",
                },
                "snippet": "Some content about foo and bar.",
            }
        ]
        with (
            patch("akasha.embeddings.embed", return_value=fake_embedding),
            patch("akasha.store.search", return_value=fake_results),
            patch("akasha.store.count", return_value=1),
        ):
            res = client.post("/search", json={"query": "foo"})

        assert res.json()["results"][0]["tags"] == ["foo", "bar", "baz"]


class TestAsk:
    def test_empty_question_returns_400(self):
        res = client.post("/ask", json={"question": ""})
        assert res.status_code == 400

    def test_no_api_key_returns_503(self):
        with patch("akasha.main.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            res = client.post("/ask", json={"question": "What is leadership?"})
        assert res.status_code == 503

    def test_no_results_returns_404(self):
        fake_embedding = [0.0] * 384
        with (
            patch("akasha.embeddings.embed", return_value=fake_embedding),
            patch("akasha.store.search", return_value=[]),
            patch("akasha.main.settings") as mock_settings,
        ):
            mock_settings.anthropic_api_key = "test-key"
            mock_settings.claude_model = "claude-sonnet-4-6"
            res = client.post("/ask", json={"question": "What is leadership?"})
        assert res.status_code == 404


class TestIngest:
    def test_nonexistent_file_returns_404(self):
        res = client.post("/ingest", json={"path": "/tmp/does_not_exist.epub"})
        assert res.status_code == 404

    def test_unsupported_format_returns_400(self, tmp_path):
        f = tmp_path / "book.docx"
        f.write_text("content")
        res = client.post("/ingest", json={"path": str(f)})
        assert res.status_code == 400

    def test_missing_api_key_returns_503(self, tmp_path):
        f = tmp_path / "book.epub"
        f.write_bytes(b"fake epub content")
        with patch("akasha.main.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            res = client.post("/ingest", json={"path": str(f)})
        assert res.status_code == 503
