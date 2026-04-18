"""Tests for storage.py — games/ filesystem layout and version archiving.

These tests redirect GAMES_DIR to a tmp_path fixture so they never touch
the real games/ directory.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def tmp_games_dir(tmp_path, monkeypatch):
    """Redirect all storage operations to a fresh tmp directory."""
    import storage
    fake_dir = tmp_path / "games"
    fake_dir.mkdir()
    monkeypatch.setattr(storage, "GAMES_DIR", str(fake_dir))
    return str(fake_dir)


class TestSaveAndLoad:
    def test_save_new_game_creates_files(self, tmp_games_dir):
        from storage import save_new_game, game_html_path, metadata_path
        html = "<!DOCTYPE html><html><body>game</body></html>"
        game_id, path = save_new_game(html, {"title": "Test", "genre": "arcade"})
        assert os.path.exists(game_html_path(game_id))
        assert os.path.exists(metadata_path(game_id))
        assert path.endswith("index.html")

    def test_save_new_game_persists_html(self, tmp_games_dir):
        from storage import save_new_game, load_game_html
        html = "<!DOCTYPE html><html><body>unique marker 1234</body></html>"
        game_id, _ = save_new_game(html, {"title": "X"})
        assert load_game_html(game_id) == html

    def test_save_new_game_persists_metadata(self, tmp_games_dir):
        from storage import save_new_game, load_metadata
        game_id, _ = save_new_game("<html>x</html>", {"title": "Alpha", "engine": "phaser"})
        meta = load_metadata(game_id)
        assert meta["title"] == "Alpha"
        assert meta["engine"] == "phaser"
        assert meta["id"] == game_id
        assert "created_at" in meta

    def test_load_missing_game_returns_none(self, tmp_games_dir):
        from storage import load_game_html
        assert load_game_html("00000000-0000-0000-0000-000000000000") is None

    def test_load_missing_metadata_returns_empty_dict(self, tmp_games_dir):
        from storage import load_metadata
        assert load_metadata("00000000-0000-0000-0000-000000000000") == {}

    def test_game_exists(self, tmp_games_dir):
        from storage import save_new_game, game_exists
        game_id, _ = save_new_game("<html></html>", {})
        assert game_exists(game_id) is True
        assert game_exists("a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12) is False


class TestOverwriteAndArchive:
    def test_overwrite_replaces_html(self, tmp_games_dir):
        from storage import save_new_game, overwrite_game_html, load_game_html
        game_id, _ = save_new_game("<html>v1</html>", {})
        overwrite_game_html(game_id, "<html>v2</html>")
        assert load_game_html(game_id) == "<html>v2</html>"

    def test_archive_creates_v1(self, tmp_games_dir):
        from storage import save_new_game, archive_current_version
        game_id, _ = save_new_game("<html>v1</html>", {})
        archived = archive_current_version(game_id, "<html>v1</html>")
        assert archived == "versions/v1.html"
        full = os.path.join(tmp_games_dir, game_id, archived)
        with open(full) as f:
            assert f.read() == "<html>v1</html>"

    def test_archive_increments(self, tmp_games_dir):
        from storage import save_new_game, archive_current_version
        game_id, _ = save_new_game("<html>x</html>", {})
        a1 = archive_current_version(game_id, "<html>a</html>")
        a2 = archive_current_version(game_id, "<html>b</html>")
        a3 = archive_current_version(game_id, "<html>c</html>")
        assert a1 == "versions/v1.html"
        assert a2 == "versions/v2.html"
        assert a3 == "versions/v3.html"


class TestListAllGames:
    def test_empty_returns_empty_list(self, tmp_games_dir):
        from storage import list_all_games
        assert list_all_games() == []

    def test_lists_saved_games(self, tmp_games_dir):
        from storage import save_new_game, list_all_games
        save_new_game("<h>a</h>", {"title": "A"})
        save_new_game("<h>b</h>", {"title": "B"})
        games = list_all_games()
        assert len(games) == 2
        titles = {g["title"] for g in games}
        assert titles == {"A", "B"}

    def test_sorted_newest_first(self, tmp_games_dir):
        """list_all_games must sort by created_at descending."""
        import storage
        # Forge two metadata files with different timestamps
        for idx, ts in enumerate(["2025-01-01T00:00:00", "2026-01-01T00:00:00"]):
            folder = os.path.join(tmp_games_dir, f"{'a'*8}-{'b'*4}-{'c'*4}-{'d'*4}-{idx:012d}")
            os.makedirs(folder)
            with open(os.path.join(folder, "metadata.json"), "w") as f:
                json.dump({"id": folder, "created_at": ts, "title": f"game-{idx}"}, f)
        games = storage.list_all_games()
        assert len(games) == 2
        assert games[0]["created_at"] > games[1]["created_at"]

    def test_skips_non_uuid_dirs(self, tmp_games_dir):
        """Stray directories shouldn't crash or appear in output."""
        from storage import list_all_games
        os.makedirs(os.path.join(tmp_games_dir, "not-a-uuid"))
        os.makedirs(os.path.join(tmp_games_dir, "also_bad"))
        assert list_all_games() == []
