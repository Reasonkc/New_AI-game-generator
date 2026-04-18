"""Tests for backend API endpoints."""

import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestEnhancePrompt:
    """Tests for POST /enhance_prompt."""

    def test_valid_prompt(self, client, mock_gemini):
        response = client.post(
            "/enhance_prompt",
            data=json.dumps({"prompt": "A platformer game with jumping"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "title" in data
        assert "description" in data
        assert "genre" in data

    def test_missing_prompt_field(self, client):
        response = client.post(
            "/enhance_prompt",
            data=json.dumps({"wrong_field": "test"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_empty_prompt(self, client):
        response = client.post(
            "/enhance_prompt",
            data=json.dumps({"prompt": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_no_json_body(self, client):
        response = client.post("/enhance_prompt", content_type="application/json")
        assert response.status_code in (400, 500)


class TestGenerateGame:
    """Tests for POST /generate_game."""

    def test_valid_object_prompt(self, client, mock_claude):
        response = client.post(
            "/generate_game",
            data=json.dumps({
                "enhanced_prompt": {
                    "title": "Test Game",
                    "description": "A test game",
                    "genre": "Action",
                    "game_mechanics": ["jump"],
                    "visual_style": "pixel",
                    "controls": "WASD",
                    "objectives": "win",
                }
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "game_id" in data
        assert "play_url" in data
        assert data["title"] == "Test Game"

    def test_valid_string_prompt(self, client, mock_claude):
        response = client.post(
            "/generate_game",
            data=json.dumps({"enhanced_prompt": "A simple shooting game"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "game_id" in data
        assert data["title"] == "AI Generated Game"

    def test_missing_enhanced_prompt(self, client):
        response = client.post(
            "/generate_game",
            data=json.dumps({"wrong": "data"}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestUpdateGame:
    """Tests for POST /update_game."""

    def test_valid_update(self, client, mock_claude):
        response = client.post(
            "/update_game",
            data=json.dumps({
                "feedback": "Add more enemies",
                "current_html": "<html><body>game</body></html>",
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "html" in response.get_json()

    def test_missing_fields(self, client):
        response = client.post(
            "/update_game",
            data=json.dumps({"feedback": "test"}),
            content_type="application/json",
        )
        assert response.status_code == 400


class TestGetGame:
    """Tests for GET /get_game/<id>."""

    def test_invalid_game_id(self, client):
        response = client.get("/get_game/invalid-id")
        assert response.status_code == 400

    def test_nonexistent_game(self, client):
        response = client.get("/get_game/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert response.status_code == 404


class TestListGames:
    """Tests for GET /list_games."""

    def test_returns_list(self, client):
        response = client.get("/list_games")
        assert response.status_code == 200
        data = response.get_json()
        assert "games" in data
        assert isinstance(data["games"], list)


class TestReportBrokenGame:
    """Tests for POST /report_broken_game."""

    def test_missing_fields(self, client):
        response = client.post(
            "/report_broken_game",
            data=json.dumps({"game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_invalid_game_id(self, client):
        response = client.post(
            "/report_broken_game",
            data=json.dumps({"game_id": "../etc", "user_description": "broken"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_description(self, client):
        response = client.post(
            "/report_broken_game",
            data=json.dumps({
                "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_description": "   ",
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_nonexistent_game(self, client):
        response = client.post(
            "/report_broken_game",
            data=json.dumps({
                "game_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "user_description": "ball does not bounce",
            }),
            content_type="application/json",
        )
        assert response.status_code == 404


class TestPlayGame:
    """Tests for GET /play_game/<id>."""

    def test_invalid_id(self, client):
        response = client.get("/play_game/not-a-uuid")
        assert response.status_code == 400

    def test_nonexistent_game(self, client):
        response = client.get("/play_game/a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        assert response.status_code == 404
