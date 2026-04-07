import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")


@pytest.fixture
def app():
    with patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
        "CLAUDE_API_KEY": "test-claude-key",
    }):
        from backend import app as flask_app
        flask_app.config["TESTING"] = True
        flask_app.config["RATELIMIT_ENABLED"] = False
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_gemini():
    with patch("backend.genai.Client") as mock:
        instance = MagicMock()
        instance.models.generate_content.return_value = MagicMock(
            text="Enhanced game concept with detailed mechanics."
        )
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_claude():
    with patch("backend.claude_client") as mock:
        mock.messages.create.return_value = MagicMock(
            content=[MagicMock(text="<!DOCTYPE html><html><body><h1>Game</h1></body></html>")]
        )
        yield mock
