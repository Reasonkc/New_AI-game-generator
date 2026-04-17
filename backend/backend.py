"""Flask application entry point — route definitions only."""

import flask
from flask import request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai
import anthropic

from config import GEMINI_API_KEY, CLAUDE_API_KEY
from utils import sanitize_game_id, extract_html_from_response
from prompts import build_enhance_prompt, build_generate_prompt, build_update_prompt
from game_storage import save_game, load_game, update_game_file, list_all_games, get_game_html_path

app = flask.Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["150 per day", "35 per hour"],
    storage_uri="memory://",
)

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/enhance_prompt', methods=['POST'])
@limiter.limit("10 per hour")
def enhance_prompt():
    """Use Gemini to refine and enhance the user's game prompt."""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400

        prompt = data['prompt']
        if not prompt or len(prompt.strip()) == 0:
            return jsonify({"error": "Prompt cannot be empty"}), 400

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=build_enhance_prompt(prompt),
        )

        return jsonify({
            "title": "AI Generated Game",
            "description": response.text,
            "genre": "Action",
            "game_mechanics": ["movement", "collision"],
            "visual_style": "Simple geometric shapes",
            "controls": "Arrow keys or WASD",
            "objectives": "Complete the game objectives",
        })

    except Exception as e:
        app.logger.error(f"Error in enhance_prompt: {e}")
        return jsonify({"error": "Failed to enhance prompt"}), 500


@app.route('/generate_game', methods=['POST'])
@limiter.limit("5 per hour")
def generate_game():
    """Use Claude to generate PhaserJS game code based on enhanced prompt."""
    try:
        data = request.get_json()
        if not data or 'enhanced_prompt' not in data:
            return jsonify({"error": "Missing 'enhanced_prompt' in request"}), 400

        enhanced_prompt = data['enhanced_prompt']

        if isinstance(enhanced_prompt, str):
            description = enhanced_prompt
            title = "AI Generated Game"
            genre = "Action"
            mechanics = "movement, collision detection"
            visual_style = "Simple geometric shapes"
            controls = "Arrow keys or WASD"
            objectives = "Complete the game objectives"
        else:
            description = enhanced_prompt.get('description', '')
            title = enhanced_prompt.get('title', 'AI Generated Game')
            genre = enhanced_prompt.get('genre', 'Action')
            mechanics = ', '.join(enhanced_prompt.get('game_mechanics', ['movement', 'collision detection']))
            visual_style = enhanced_prompt.get('visual_style', 'Simple geometric shapes')
            controls = enhanced_prompt.get('controls', 'Arrow keys or WASD')
            objectives = enhanced_prompt.get('objectives', 'Complete the game objectives')

        claude_prompt = build_generate_prompt(
            title, description, genre, mechanics, visual_style, controls, objectives
        )

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20000,
            temperature=0.7,
            messages=[{"role": "user", "content": claude_prompt}],
        )

        game_html = extract_html_from_response(response.content[0].text)
        result = save_game(game_html, title, description, genre)
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in generate_game: {e}")
        return jsonify({"error": "Failed to generate game"}), 500


@app.route('/update_game', methods=['POST'])
@limiter.limit("5 per hour")
def update_game():
    """Update an existing game based on feedback."""
    try:
        data = request.get_json()
        if not data or 'feedback' not in data or 'current_html' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        feedback = data["feedback"]
        current_html = data["current_html"]
        game_id = data.get("game_id")

        claude_prompt = build_update_prompt(current_html, feedback)

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=32000,
            temperature=0.7,
            messages=[{"role": "user", "content": claude_prompt}],
        )

        updated_html = extract_html_from_response(response.content[0].text)

        if game_id:
            try:
                update_game_file(game_id, updated_html)
            except ValueError:
                pass

        return jsonify({"html": updated_html})

    except Exception as e:
        app.logger.error(f"Error in update_game: {e}")
        return jsonify({"error": "Failed to update game"}), 500


@app.route("/get_game/<game_id>", methods=["GET"])
def get_game(game_id):
    """Retrieve a saved game by ID."""
    try:
        game = load_game(game_id)
        return jsonify(game)
    except ValueError:
        return jsonify({"error": "Invalid game ID"}), 400
    except FileNotFoundError:
        return jsonify({"error": "Game not found"}), 404
    except Exception as e:
        app.logger.error(f"Error in get_game: {e}")
        return jsonify({"error": "Failed to retrieve game"}), 500


@app.route("/list_games", methods=["GET"])
def list_games():
    """List all saved games."""
    try:
        return jsonify({"games": list_all_games()})
    except Exception as e:
        app.logger.error(f"Error in list_games: {e}")
        return jsonify({"error": "Failed to list games"}), 500


@app.route('/play_game/<game_id>', methods=['GET'])
def play_game(game_id):
    """Serve the game HTML directly for playing with CSP protection."""
    try:
        game_path = get_game_html_path(game_id)
        response = flask.make_response(send_file(game_path))
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response
    except ValueError:
        return "Invalid game ID", 400
    except FileNotFoundError:
        return "Game not found", 404
    except Exception as e:
        app.logger.error(f"Error in play_game: {e}")
        return "Error loading game", 500


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
