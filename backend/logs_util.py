"""Append-only JSONL log writer for generation + bug-report events."""
import json
import logging

logger = logging.getLogger(__name__)


def append_jsonl(path: str, entry: dict) -> None:
    """Append a single JSON object as one line. Failures are logged, never raised."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write log {path}: {e}")
