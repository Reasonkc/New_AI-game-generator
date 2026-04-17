"""Filesystem persistence for games, metadata, and version archives.

Single source of truth for the games/ directory layout:
    games/<uuid>/index.html
    games/<uuid>/metadata.json
    games/<uuid>/generation_log.json
    games/<uuid>/versions/v<N>.html  (archives, created on bug-report overwrites)

Route handlers call these helpers instead of touching os.path directly.
"""
import json
import os
import re
import uuid
from datetime import datetime

from config import GAMES_DIR


def game_folder(game_id: str) -> str:
    return os.path.join(GAMES_DIR, game_id)


def game_html_path(game_id: str) -> str:
    return os.path.join(game_folder(game_id), "index.html")


def metadata_path(game_id: str) -> str:
    return os.path.join(game_folder(game_id), "metadata.json")


def save_new_game(html: str, fields: dict) -> tuple[str, str]:
    """Persist a freshly-generated game. Returns (game_id, html_path)."""
    game_id = str(uuid.uuid4())
    folder = game_folder(game_id)
    os.makedirs(folder, exist_ok=True)

    html_path = game_html_path(game_id)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    metadata = {
        "id": game_id,
        "created_at": datetime.now().isoformat(),
        "file_path": html_path,
        **fields,
    }
    with open(metadata_path(game_id), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return game_id, html_path


def save_generation_log(game_id: str, log: dict) -> None:
    path = os.path.join(game_folder(game_id), "generation_log.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


def game_exists(game_id: str) -> bool:
    return os.path.exists(game_html_path(game_id))


def load_game_html(game_id: str) -> str | None:
    path = game_html_path(game_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_metadata(game_id: str) -> dict:
    path = metadata_path(game_id)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def overwrite_game_html(game_id: str, html: str) -> None:
    with open(game_html_path(game_id), "w", encoding="utf-8") as f:
        f.write(html)


def list_all_games() -> list[dict]:
    """Return all saved games, newest first. Skips anything that doesn't look like a UUID."""
    games: list[dict] = []
    if not os.path.exists(GAMES_DIR):
        return games
    uuid_re = re.compile(r'^[a-f0-9-]{36}$')
    for entry in os.listdir(GAMES_DIR):
        if not uuid_re.match(entry):
            continue
        meta = load_metadata(entry)
        if meta:
            games.append(meta)
    games.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return games


def archive_current_version(game_id: str, html_to_archive: str) -> str:
    """Copy the soon-to-be-overwritten HTML to versions/v<N>.html. Returns relative path."""
    versions_dir = os.path.join(game_folder(game_id), "versions")
    os.makedirs(versions_dir, exist_ok=True)
    version_re = re.compile(r'^v(\d+)\.html$')
    existing = [n for n in os.listdir(versions_dir) if version_re.match(n)]
    next_n = 1 + max(
        (int(version_re.match(n).group(1)) for n in existing),
        default=0,
    )
    archive_path = os.path.join(versions_dir, f"v{next_n}.html")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(html_to_archive)
    return f"versions/v{next_n}.html"
