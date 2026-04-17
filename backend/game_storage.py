"""Game file storage operations (save, load, list, serve)."""

import json
import os
import uuid
from datetime import datetime

from config import GAMES_DIR
from utils import sanitize_game_id


def save_game(game_html: str, title: str, description: str, genre: str) -> dict:
    """Save a generated game to disk with metadata.

    Returns:
        dict with game_id, title, status, and play_url.
    """
    game_id = str(uuid.uuid4())
    game_folder = os.path.join(GAMES_DIR, game_id)
    os.makedirs(game_folder, exist_ok=True)

    game_path = os.path.join(game_folder, "index.html")
    with open(game_path, "w", encoding="utf-8") as f:
        f.write(game_html)

    metadata = {
        "id": game_id,
        "title": title,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "genre": genre,
        "file_path": game_path,
    }

    metadata_path = os.path.join(game_folder, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "game_id": game_id,
        "title": title,
        "status": "created",
        "play_url": f"/play_game/{game_id}",
    }


def load_game(game_id: str) -> dict:
    """Load a game's HTML and metadata by ID.

    Raises:
        ValueError: If game_id is invalid.
        FileNotFoundError: If the game does not exist.
    """
    game_id = sanitize_game_id(game_id)
    game_path = os.path.join(GAMES_DIR, game_id, "index.html")
    metadata_path = os.path.join(GAMES_DIR, game_id, "metadata.json")

    if not os.path.exists(game_path):
        raise FileNotFoundError("Game not found")

    with open(game_path, "r", encoding="utf-8") as f:
        html = f.read()

    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return {"game_id": game_id, "html": html, "metadata": metadata}


def update_game_file(game_id: str, html: str) -> None:
    """Overwrite a saved game's HTML file."""
    game_id = sanitize_game_id(game_id)
    game_folder = os.path.join(GAMES_DIR, game_id)
    if os.path.exists(game_folder):
        game_path = os.path.join(game_folder, "index.html")
        with open(game_path, "w", encoding="utf-8") as f:
            f.write(html)


def list_all_games() -> list[dict]:
    """List all saved games sorted by creation date (newest first)."""
    games = []
    if not os.path.exists(GAMES_DIR):
        return games

    for entry in os.listdir(GAMES_DIR):
        try:
            entry = sanitize_game_id(entry)
            metadata_path = os.path.join(GAMES_DIR, entry, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    games.append(json.load(f))
        except (ValueError, json.JSONDecodeError):
            continue

    games.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return games


def get_game_html_path(game_id: str) -> str:
    """Get the file path for a game's HTML file.

    Raises:
        ValueError: If game_id is invalid.
        FileNotFoundError: If the game does not exist.
    """
    game_id = sanitize_game_id(game_id)
    game_path = os.path.join(GAMES_DIR, game_id, "index.html")
    if not os.path.exists(game_path):
        raise FileNotFoundError("Game not found")
    return game_path
