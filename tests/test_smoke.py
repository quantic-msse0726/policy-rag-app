"""
Smoke tests for the Policy RAG app. No API keys required.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    """GET /health returns {"status":"ok"}."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_returns_chat_ui():
    """GET / returns HTML with Policy RAG Chat."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Policy RAG Chat" in resp.text


def test_chat_unanswerable_returns_refusal():
    """POST /chat with unanswerable question returns refusal, empty citations/snippets."""
    with patch("app.main.retrieve", return_value=[]):
        resp = client.post(
            "/chat",
            json={"question": "What is today's cafeteria menu?"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["citations"] == []
    assert data["snippets"] == []
    assert "cannot" in data["answer"].lower()
