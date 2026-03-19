import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock environment variables before importing the app
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-claude-key")


@pytest.fixture
def app():
    """Create Flask test application."""
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
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def mock_gemini():
    """Mock Google Gemini API client."""
    with patch("backend.genai.Client") as mock:
        instance = MagicMock()
        instance.models.generate_content.return_value = MagicMock(
            text="Enhanced game concept with detailed mechanics and controls."
        )
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_claude():
    """Mock Anthropic Claude API client."""
    with patch("backend.claude_client") as mock:
        mock.messages.create.return_value = MagicMock(
            content=[MagicMock(text="<!DOCTYPE html><html><body><h1>Game</h1></body></html>")]
        )
        yield mock
