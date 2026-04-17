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
    """Mock the Claude client. Supports both .messages.create() and .messages.stream().

    For streaming, each call to .stream(...) returns a fresh context manager whose
    text_stream iterator yields the seed Pong example — enough to pass validation.
    """
    seed_path = os.path.join(os.path.dirname(__file__), "..", "seed_example.html")
    with open(seed_path, "r", encoding="utf-8") as f:
        seed_html = f.read()

    def make_stream_ctx(*args, **kwargs):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.text_stream = iter([seed_html])
        ctx.get_final_message.return_value = MagicMock(
            usage=MagicMock(input_tokens=100, output_tokens=200)
        )
        return ctx

    with patch("backend.claude_client") as mock:
        mock.messages.stream.side_effect = make_stream_ctx
        mock.messages.create.return_value = MagicMock(
            content=[MagicMock(text=seed_html)]
        )
        yield mock
