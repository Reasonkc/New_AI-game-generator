"""Tests for utility functions: sanitize_game_id() and extract_html_from_response()."""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSanitizeGameId:
    def test_valid_uuid(self, app):
        from backend import sanitize_game_id
        valid_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        assert sanitize_game_id(valid_id) == valid_id

    def test_rejects_path_traversal(self, app):
        from backend import sanitize_game_id
        with pytest.raises(ValueError):
            sanitize_game_id("../../../etc/passwd")

    def test_rejects_empty_string(self, app):
        from backend import sanitize_game_id
        with pytest.raises(ValueError):
            sanitize_game_id("")

    def test_rejects_short_id(self, app):
        from backend import sanitize_game_id
        with pytest.raises(ValueError):
            sanitize_game_id("abc123")

    def test_rejects_uppercase(self, app):
        from backend import sanitize_game_id
        with pytest.raises(ValueError):
            sanitize_game_id("A1B2C3D4-E5F6-7890-ABCD-EF1234567890")

    def test_rejects_special_characters(self, app):
        from backend import sanitize_game_id
        with pytest.raises(ValueError):
            sanitize_game_id("a1b2c3d4-e5f6-7890-abcd-ef123456789;")


class TestExtractHtmlFromResponse:
    def test_strips_html_code_fence(self, app):
        from backend import extract_html_from_response
        text = "```html\n<!DOCTYPE html><html><body>Test</body></html>\n```"
        result = extract_html_from_response(text)
        assert result.startswith("<!DOCTYPE html>")
        assert "```" not in result

    def test_no_fence_passthrough(self, app):
        from backend import extract_html_from_response
        text = "<!DOCTYPE html><html><body>Test</body></html>"
        assert extract_html_from_response(text) == text

    def test_strips_whitespace(self, app):
        from backend import extract_html_from_response
        text = "  \n<!DOCTYPE html><html><body>Test</body></html>\n  "
        result = extract_html_from_response(text)
        assert result.startswith("<!DOCTYPE html>")

    def test_preserves_inner_content(self, app):
        from backend import extract_html_from_response
        text = "```html\n<!DOCTYPE html><html><body><script>var x = 1;</script></body></html>\n```"
        result = extract_html_from_response(text)
        assert "var x = 1;" in result
