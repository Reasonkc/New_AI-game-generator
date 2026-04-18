"""Tests for llm.py — streaming wrapper and two-pass generation with retry.

Uses the Pong seed HTML (which passes validate_game_html) as the happy-path
fixture output. Mocks the Anthropic client's streaming context manager.
"""
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "seed_example.html")
with open(SEED_PATH, "r", encoding="utf-8") as _f:
    SEED_HTML = _f.read()


def _make_stream_ctx(chunks: list[str], input_tokens: int = 100, output_tokens: int = 200):
    """Build a MagicMock that imitates Claude's streaming context manager."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.text_stream = iter(chunks)
    ctx.get_final_message.return_value = MagicMock(
        usage=MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    )
    return ctx


def _make_client(*response_sets):
    """Build a mock Claude client whose .messages.stream yields the next response set on each call."""
    client = MagicMock()
    iterator = iter(response_sets)

    def side_effect(*args, **kwargs):
        chunks = next(iterator)
        return _make_stream_ctx(chunks)

    client.messages.stream.side_effect = side_effect
    return client


class TestAccum:
    def test_accumulates_tokens(self):
        from llm import _accum
        a = {"input_tokens": 10, "output_tokens": 20}
        _accum(a, {"input_tokens": 3, "output_tokens": 4})
        assert a == {"input_tokens": 13, "output_tokens": 24}

    def test_handles_missing_keys(self):
        from llm import _accum
        a = {}
        _accum(a, {"input_tokens": 5, "output_tokens": 6})
        assert a == {"input_tokens": 5, "output_tokens": 6}


class TestStreamClaude:
    def test_concatenates_chunks(self):
        from llm import _stream_claude
        client = _make_client(["hello ", "world"])
        text, usage = _stream_claude(client, messages=[{"role": "user", "content": "x"}], system="sys")
        assert text == "hello world"
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 200


class TestGenerateGameWithRetry:
    def test_happy_path_returns_html(self):
        from llm import generate_game_with_retry
        # Two calls per attempt (generate + self-review). One attempt total by default.
        client = _make_client([SEED_HTML], [SEED_HTML])
        html, attempts, warnings, usage = generate_game_with_retry(
            client=client,
            user_prompt_text="build a pong game",
            engine_key="phaser",
            genre="arcade",
        )
        assert html.startswith("<!DOCTYPE html>")
        assert len(attempts) == 1
        assert attempts[0]["passed"] is True
        assert warnings == []
        assert usage["input_tokens"] > 0

    def test_retry_with_max_retries_env(self, monkeypatch):
        """With max_retries=2, a failing first attempt should lead to a second attempt."""
        from llm import generate_game_with_retry
        import llm
        monkeypatch.setitem(llm.GENERATION_CONFIG, "max_retries", 2)

        # Attempt 1: both passes return an empty/invalid html. Attempt 2: both return seed.
        bad = "<html>too short</html>"
        client = _make_client([bad], [bad], [SEED_HTML], [SEED_HTML])
        html, attempts, warnings, usage = generate_game_with_retry(
            client=client,
            user_prompt_text="pong",
            engine_key="phaser",
            genre="arcade",
        )
        assert len(attempts) == 2
        assert attempts[0]["passed"] is False
        assert attempts[1]["passed"] is True
        assert warnings == []
        assert html.startswith("<!DOCTYPE html>")

    def test_all_attempts_fail_returns_best_with_warnings(self, monkeypatch):
        from llm import generate_game_with_retry
        import llm
        monkeypatch.setitem(llm.GENERATION_CONFIG, "max_retries", 1)

        bad = "<html>nope</html>"
        client = _make_client([bad], [bad])
        html, attempts, warnings, usage = generate_game_with_retry(
            client=client,
            user_prompt_text="pong",
            engine_key="phaser",
            genre="arcade",
        )
        assert attempts[0]["passed"] is False
        assert len(warnings) > 0
        assert any("failed validation" in w for w in warnings)

    def test_threejs_engine_uses_3d_prompt(self):
        """Verify engine_key='threejs' routes to the 3D system prompt without crashing."""
        from llm import generate_game_with_retry
        client = _make_client([SEED_HTML], [SEED_HTML])
        # 2D seed will fail 3D validation (no WebGLRenderer), that's fine — we only care
        # that the 3D prompt path executes without error.
        _, attempts, _, _ = generate_game_with_retry(
            client=client,
            user_prompt_text="racing game",
            engine_key="threejs",
            genre="arcade",
        )
        assert len(attempts) >= 1
        # Check system_prompt was the 3D one: inspect the first stream call's kwargs
        call_args = client.messages.stream.call_args_list[0]
        assert "Three.js" in call_args.kwargs["system"]
