"""Utility functions for input validation and response processing."""

import re


def sanitize_game_id(game_id: str) -> str:
    """Validate game_id to prevent path traversal attacks."""
    if not re.match(r'^[a-f0-9-]{36}$', game_id):
        raise ValueError("Invalid game ID format")
    return game_id


def extract_html_from_response(text: str) -> str:
    """Extract HTML from Claude's response, stripping markdown code fences.

    Args:
        text: Raw response text from Claude API.

    Returns:
        Cleaned HTML string.

    Raises:
        ValueError: If the input is empty or not a string.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Response text must be a non-empty string")

    original_length = len(text)

    # Strip markdown code fences in one pass
    cleaned_text = re.sub(
        r'```(?:html)?\s*\n?(.*?)\n?```',
        r'\1',
        text,
        flags=re.DOTALL
    ).strip()

    if cleaned_text == text.strip():
        cleaned_text = text.strip()

    # Validation warnings (logged by caller)
    warnings = []
    if not cleaned_text.lower().startswith('<!doctype') and '<html' not in cleaned_text.lower():
        warnings.append("Response does not appear to contain valid HTML")
    if not cleaned_text.lower().endswith('</html>'):
        warnings.append("HTML response appears to be truncated - missing closing </html> tag")
    if cleaned_text.endswith('...'):
        warnings.append("Response appears to be truncated (ends with ...)")

    return cleaned_text
