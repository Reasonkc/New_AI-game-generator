"""Flask HTTP layer — thin route handlers that wire the modules together.

Business logic lives in dedicated modules:
    config.py     — env vars, GENERATION_CONFIG, API clients
    prompts.py    — system prompts (2D + 3D) with seed example
    validation.py — pure validators (sanitize_game_id, validate_game_html, ...)
    llm.py        — Claude two-pass generation + retry
    storage.py    — games/ filesystem operations
    logs_util.py  — append-only JSONL writer

This file parses requests, delegates to the helpers, and formats responses.
"""
import os
import time
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    """Timezone-aware UTC timestamp in ISO-8601 with a trailing 'Z'."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

import flask
from flask import request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from google import genai


GEMINI_MODELS = ("gemini-2.5-flash", "gemini-2.5-pro")
GEMINI_RETRIES_PER_MODEL = 3
GEMINI_BACKOFF_BASE_S = 0.8


def _call_gemini_with_fallback(query: str) -> str:
    """Call Gemini with retry+backoff on 503, falling back to the next model."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    last_err: Exception | None = None
    for model in GEMINI_MODELS:
        for attempt in range(GEMINI_RETRIES_PER_MODEL):
            try:
                return client.models.generate_content(model=model, contents=query).text
            except Exception as e:
                msg = str(e)
                transient = "503" in msg or "UNAVAILABLE" in msg or "overloaded" in msg.lower()
                last_err = e
                if not transient:
                    raise
                if attempt < GEMINI_RETRIES_PER_MODEL - 1:
                    time.sleep(GEMINI_BACKOFF_BASE_S * (2 ** attempt))
    assert last_err is not None
    raise last_err

from config import (
    GEMINI_API_KEY,
    GENERATIONS_LOG,
    BUG_REPORTS_LOG,
    claude_client,
)
from prompts import GAME_SYSTEM_PROMPT_2D, GAME_SYSTEM_PROMPT_3D
from validation import (
    sanitize_game_id,
    extract_html_from_response,
    detect_genre,
    validate_game_html,
)
from llm import _stream_claude, generate_game_with_retry
from storage import (
    save_new_game,
    save_generation_log,
    game_html_path,
    load_game_html,
    load_metadata,
    overwrite_game_html,
    list_all_games,
    archive_current_version,
    game_exists,
)
from logs_util import append_jsonl


app = flask.Flask(__name__)
CORS(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["150 per day", "35 per hour"],
    storage_uri="memory://",
)


@app.route('/enhance_prompt', methods=['POST'])
@limiter.limit("10 per hour")
def enhance_prompt():
    """Refine the user's game idea into a structured concept via Gemini."""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400

        prompt = data['prompt']
        engine = data.get('engine', 'phaser')
        if not prompt or len(prompt.strip()) == 0:
            return jsonify({"error": "Prompt cannot be empty"}), 400

        if engine == "threejs":
            engine_context = (
                "The game will be built as a 3D browser game using Three.js.\n"
                "Think in terms of 3D space: camera angles, lighting, 3D models made from basic geometries (boxes, cylinders, spheres).\n"
                "Suitable genres: driving, parking, simulation, racing, flight, 3D exploration, tower defense with 3D view.\n"
                "Controls should consider 3D movement (forward/backward, turning, camera rotation)."
            )
        else:
            engine_context = (
                "The game will be built as a 2D browser game using PhaserJS.\n"
                "Think in terms of 2D space: side-scrolling, top-down, or fixed-screen views.\n"
                "Suitable genres: platformers, shooters, puzzles, arcade, match-3, endless runners.\n"
                "All sprites will be created programmatically or loaded from free sprite libraries."
            )

        query = f"""You are an expert game designer. Transform the user's raw idea into a polished, implementable game concept.

ENGINE CONTEXT:
{engine_context}

USER'S IDEA: {prompt}

IMPORTANT — Identify the actual game the user wants. If they mention a classic (Pacman, Tetris, Snake, Breakout, Space Invaders, Flappy Bird, etc.), design the concept around THAT specific game's mechanics. Don't drift into a generic shooter or platformer if the user asked for something specific.

Your response MUST include ALL of the following clearly labeled sections:

**TITLE:** A creative, catchy game title (not generic like "AI Game")

**GENRE:** The specific game genre — be precise (e.g., "Top-down maze arcade", "Side-scrolling platformer", "Grid-based puzzle", "Space shooter with waves")

**DESCRIPTION:** A 3-paragraph game description covering:
- Core gameplay loop (what does the player do moment-to-moment?)
- Progression and difficulty (how does it escalate?)
- Win/lose conditions (how does the game end?)

**GAME MECHANICS:** Specific mechanics for THIS genre:
- Exact player movement (grid-based? free? physics-based?)
- Enemy/obstacle behavior (patrol? chase? random? AI pattern?)
- Scoring system (points per action)
- Power-ups or special abilities (if any)
- Collision and interaction rules

**VISUAL STYLE:** Visual aesthetic (colors, mood, perspective — top-down, side-scrolling, etc.)

**CONTROLS:** Exact control scheme (arrow keys for movement, spacebar for action, etc.)

**OBJECTIVES:** Primary objective and secondary objectives

Keep it concrete and implementable. No music, no sound design."""

        response_text = _call_gemini_with_fallback(query)

        title = "AI Generated Game"
        genre = "Action"
        visual_style = "Detailed and polished"
        controls = "Arrow keys or WASD"
        objectives = "Complete the game objectives"
        for line in response_text.split('\n'):
            line_clean = line.strip().replace('**', '')
            upper = line_clean.upper()
            if upper.startswith('TITLE:'):
                title = line_clean.split(':', 1)[1].strip()
            elif upper.startswith('GENRE:'):
                genre = line_clean.split(':', 1)[1].strip()
            elif upper.startswith('VISUAL STYLE:'):
                visual_style = line_clean.split(':', 1)[1].strip()
            elif upper.startswith('CONTROLS:'):
                controls = line_clean.split(':', 1)[1].strip()
            elif upper.startswith('OBJECTIVES:'):
                objectives = line_clean.split(':', 1)[1].strip()

        return jsonify({
            "title": title,
            "description": response_text,
            "genre": genre,
            "game_mechanics": ["movement", "collision", "scoring"],
            "visual_style": visual_style,
            "controls": controls,
            "objectives": objectives,
        })

    except Exception as e:
        app.logger.error(f"Error in enhance_prompt: {str(e)}")
        msg = str(e)
        if "503" in msg or "UNAVAILABLE" in msg:
            return jsonify({"error": "Prompt service is temporarily overloaded. Please try again in a moment."}), 503
        return jsonify({"error": "Failed to enhance prompt"}), 500


@app.route('/generate_game', methods=['POST'])
@limiter.limit("5 per hour")
def generate_game():
    """Generate a playable HTML game via two-pass LLM + validate + retry pipeline."""
    start_ts = time.time()
    try:
        data = request.get_json()
        if not data or 'enhanced_prompt' not in data:
            return jsonify({"error": "Missing 'enhanced_prompt' in request"}), 400

        enhanced_prompt = data['enhanced_prompt']
        engine = data.get('engine', 'phaser')

        if isinstance(enhanced_prompt, str):
            description = enhanced_prompt
            title = "AI Generated Game"
            genre_label = "Action"
            mechanics = "movement, collision detection"
            visual_style = "Simple geometric shapes"
            controls = "Arrow keys or WASD"
            objectives = "Complete the game objectives"
            raw_request_text = enhanced_prompt
        else:
            description = enhanced_prompt.get('description', '')
            title = enhanced_prompt.get('title', 'AI Generated Game')
            genre_label = enhanced_prompt.get('genre', 'Action')
            mechanics = ', '.join(enhanced_prompt.get('game_mechanics', ['movement', 'collision detection']))
            visual_style = enhanced_prompt.get('visual_style', 'Simple geometric shapes')
            controls = enhanced_prompt.get('controls', 'Arrow keys or WASD')
            objectives = enhanced_prompt.get('objectives', 'Complete the game objectives')
            raw_request_text = f"{title} {genre_label} {description}"

        detected_genre = detect_genre(raw_request_text)
        user_prompt_text = (
            f"CONCEPT: {title} ({genre_label})\n"
            f"{description}\n"
            f"Mechanics: {mechanics}\n"
            f"Controls: {controls}\n"
            f"Objectives: {objectives}\n"
            f"Visual Style: {visual_style}"
        )

        game_html, attempts, warnings, total_usage = generate_game_with_retry(
            client=claude_client,
            user_prompt_text=user_prompt_text,
            engine_key=engine,
            genre=detected_genre,
        )

        if not game_html:
            append_jsonl(GENERATIONS_LOG, {
                "timestamp": _utc_now_iso(),
                "user_request": raw_request_text[:500],
                "engine": engine,
                "detected_genre": detected_genre,
                "attempts": attempts,
                "success": False,
                "warnings": warnings or ["no html produced"],
                "total_usage": total_usage,
                "latency_s": round(time.time() - start_ts, 2),
            })
            return jsonify({"error": "Failed to generate game"}), 500

        game_id, _ = save_new_game(game_html, {
            "title": title,
            "description": description,
            "genre": genre_label,
            "detected_genre": detected_genre,
            "engine": engine,
        })
        _invalidate_list_games_cache()
        save_generation_log(game_id, {
            "game_id": game_id,
            "engine": engine,
            "detected_genre": detected_genre,
            "attempts": attempts,
            "warnings": warnings,
            "total_usage": total_usage,
            "latency_s": round(time.time() - start_ts, 2),
        })
        append_jsonl(GENERATIONS_LOG, {
            "timestamp": _utc_now_iso(),
            "game_id": game_id,
            "user_request": raw_request_text[:500],
            "engine": engine,
            "detected_genre": detected_genre,
            "attempts": attempts,
            "success": len(warnings) == 0,
            "warnings": warnings,
            "total_usage": total_usage,
            "latency_s": round(time.time() - start_ts, 2),
        })

        return jsonify({
            "game_id": game_id,
            "title": title,
            "status": "created",
            "play_url": f"/play_game/{game_id}",
            "attempts": len(attempts),
            "warnings": warnings,
            "genre": detected_genre,
        })

    except Exception as e:
        app.logger.error(f"Error in generate_game: {str(e)}")
        return jsonify({"error": "Failed to generate game"}), 500


@app.route('/update_game', methods=['POST'])
@limiter.limit("5 per hour")
def update_game():
    """Modify an existing game based on user feedback."""
    try:
        data = request.get_json()
        if not data or 'feedback' not in data or 'current_html' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        feedback = data["feedback"]
        current_html = data["current_html"]
        game_id = data.get("game_id")

        claude_prompt = f"""Here is the current HTML game code:

{current_html}

Please update the game based on this feedback: {feedback}

RULES:
1. Return the COMPLETE updated HTML file — do not omit any sections
2. Keep all existing working code — only change what the feedback asks for
3. You may load free sprites from https://labs.phaser.io/assets/ if it improves visuals
4. For programmatic textures: use this.make.graphics({{ add: false }}), .generateTexture('key', w, h), .destroy()
5. NEVER do sprite.setTexture(graphics.generateTexture()) — this causes black screens
6. Add visual polish: tweens, screen shake, color flashes for feedback
7. ZERO JavaScript errors — the game must work immediately after update

Return ONLY the complete updated HTML file. No explanations, no markdown."""

        result_text = ""
        with claude_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            temperature=0.7,
            messages=[{"role": "user", "content": claude_prompt}],
        ) as stream:
            for text in stream.text_stream:
                result_text += text

        updated_html = extract_html_from_response(result_text)

        if game_id:
            try:
                sanitize_game_id(game_id)
                if game_exists(game_id):
                    overwrite_game_html(game_id, updated_html)
            except ValueError:
                pass

        return jsonify({"html": updated_html})

    except Exception as e:
        app.logger.error(f"Error in update_game: {str(e)}")
        return jsonify({"error": "Failed to update game"}), 500


@app.route('/report_broken_game', methods=['POST'])
@limiter.limit("5 per hour")
def report_broken_game():
    """Accept a bug report, ask Claude to fix, validate, archive prior version, save the fix."""
    start_ts = time.time()
    try:
        data = request.get_json()
        if not data or 'game_id' not in data or 'user_description' not in data:
            return jsonify({"error": "Missing 'game_id' or 'user_description'"}), 400

        try:
            game_id = sanitize_game_id(data['game_id'])
        except ValueError:
            return jsonify({"error": "Invalid game ID"}), 400

        description = (data.get('user_description') or '').strip()
        if not description:
            return jsonify({"error": "user_description cannot be empty"}), 400

        current_html = load_game_html(game_id)
        if current_html is None:
            return jsonify({"error": "Game not found"}), 404

        metadata = load_metadata(game_id)
        engine = metadata.get("engine") or "phaser"
        engine_tag = "3d" if engine == "threejs" else "2d"
        system_prompt = GAME_SYSTEM_PROMPT_3D if engine_tag == "3d" else GAME_SYSTEM_PROMPT_2D

        messages = [
            {"role": "user", "content": (
                f"This game has a reported bug: {description}\n\n"
                "Fix it while keeping all 14 technical requirements from the system prompt satisfied. "
                "Output only the corrected HTML file. No explanation, no markdown fences."
            )},
            {"role": "assistant", "content": current_html},
            {"role": "user", "content": (
                "Return the complete corrected HTML now. Preserve working gameplay. "
                "Output ONLY the HTML."
            )},
        ]

        try:
            fixed_text, usage = _stream_claude(claude_client, messages=messages, system=system_prompt)
        except Exception as e:
            app.logger.error(f"report_broken_game LLM error: {e}")
            return jsonify({"error": "Failed to contact model"}), 502

        fixed_html = extract_html_from_response(fixed_text)
        passed, failures = validate_game_html(fixed_html, engine=engine_tag)
        warnings = [] if passed else failures

        if not fixed_html or len(fixed_html) < 2000:
            append_jsonl(BUG_REPORTS_LOG, {
                "timestamp": _utc_now_iso(),
                "game_id": game_id,
                "description": description[:500],
                "engine": engine,
                "applied": False,
                "warnings": ["fix output too short or empty"] + failures,
                "usage": usage,
                "latency_s": round(time.time() - start_ts, 2),
            })
            return jsonify({
                "game_id": game_id,
                "status": "fix_rejected",
                "play_url": f"/play_game/{game_id}",
                "warnings": ["fix output too short or empty"] + failures,
            }), 200

        archived_as = archive_current_version(game_id, current_html)
        overwrite_game_html(game_id, fixed_html)

        append_jsonl(BUG_REPORTS_LOG, {
            "timestamp": _utc_now_iso(),
            "game_id": game_id,
            "description": description[:500],
            "engine": engine,
            "archived_as": archived_as,
            "applied": True,
            "validation_passed": passed,
            "warnings": warnings,
            "usage": usage,
            "latency_s": round(time.time() - start_ts, 2),
        })

        return jsonify({
            "game_id": game_id,
            "status": "fixed",
            "play_url": f"/play_game/{game_id}",
            "archived_as": archived_as,
            "warnings": warnings,
        })

    except Exception as e:
        app.logger.error(f"Error in report_broken_game: {e}")
        return jsonify({"error": "Failed to process bug report"}), 500


@app.route('/suggest_improvements', methods=['POST'])
@limiter.limit("20 per hour")
def suggest_improvements():
    """Return a small set of clickable suggestions to improve a generated game.

    Combines static validator signals (definite fixes for detected breakage) with
    Gemini-proposed polish ideas grounded in the actual HTML. Each suggestion has
    a short label the UI can show as a chip, and a `prompt` the user can send
    through /update_game.
    """
    try:
        data = request.get_json() or {}
        game_id = data.get("game_id")
        html = data.get("html")
        engine = (data.get("engine") or "phaser").lower()
        engine_tag = "3d" if engine == "threejs" else "2d"

        if game_id and not html:
            try:
                sanitize_game_id(game_id)
            except ValueError:
                return jsonify({"error": "Invalid game ID"}), 400
            html = load_game_html(game_id)
            if html is None:
                return jsonify({"error": "Game not found"}), 404
            metadata = load_metadata(game_id)
            if metadata.get("engine"):
                engine_tag = "3d" if metadata["engine"] == "threejs" else "2d"

        if not html:
            return jsonify({"error": "Missing 'game_id' or 'html'"}), 400

        fixes: list[dict] = []
        passed, failures = validate_game_html(html, engine=engine_tag)
        if not passed:
            summary = "; ".join(failures[:3])
            fixes.append({
                "kind": "fix",
                "label": "Fix detected issues",
                "prompt": (
                    "The game currently has these problems that must be fixed: "
                    f"{summary}. Please repair these while preserving all working gameplay."
                ),
            })

        snippet = html[:8000]
        engine_hint = "Three.js r128 3D game" if engine_tag == "3d" else "2D Phaser/canvas game"
        query = f"""You are a senior game developer reviewing a generated {engine_hint} HTML file.

Propose EXACTLY 3 concrete, high-impact improvements a non-technical user could request. Each must be specific to what you see in the code (not generic advice).

Categories to consider: visual polish (particles, screen shake, color flashes), graphics (lighting/shadows for 3D, sprite quality for 2D), game feel (tweens, easing, sound cues — no audio though), mechanics (difficulty curve, enemy variety), controls.

Return ONLY a JSON array, no prose, no markdown fences. Each item: {{"label": "<=5 word chip title", "prompt": "one-sentence instruction for the developer to implement"}}.

CODE (truncated):
{snippet}"""

        try:
            raw = _call_gemini_with_fallback(query)
        except Exception as e:
            app.logger.warning(f"suggest_improvements gemini failed: {e}")
            raw = ""

        ideas: list[dict] = []
        if raw:
            import json, re as _re
            m = _re.search(r'\[[\s\S]*\]', raw)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                    if isinstance(parsed, list):
                        for item in parsed[:3]:
                            label = (item.get("label") or "").strip()
                            prompt_text = (item.get("prompt") or "").strip()
                            if label and prompt_text:
                                ideas.append({
                                    "kind": "improve",
                                    "label": label[:40],
                                    "prompt": prompt_text[:400],
                                })
                except (json.JSONDecodeError, AttributeError):
                    pass

        return jsonify({
            "suggestions": fixes + ideas,
            "has_issues": bool(fixes),
            "validator_warnings": failures,
        })

    except Exception as e:
        app.logger.error(f"Error in suggest_improvements: {e}")
        return jsonify({"error": "Failed to produce suggestions"}), 500


@app.route("/get_game/<game_id>", methods=["GET"])
def get_game(game_id):
    """Retrieve a saved game by ID."""
    try:
        game_id = sanitize_game_id(game_id)
        html = load_game_html(game_id)
        if html is None:
            return jsonify({"error": "Game not found"}), 404
        metadata = load_metadata(game_id)
        return jsonify({"game_id": game_id, "html": html, "metadata": metadata})
    except ValueError:
        return jsonify({"error": "Invalid game ID"}), 400
    except Exception as e:
        app.logger.error(f"Error in get_game: {str(e)}")
        return jsonify({"error": "Failed to retrieve game"}), 500


_LIST_GAMES_CACHE: dict = {"expires_at": 0.0, "games": None}
_LIST_GAMES_TTL_S = 30.0


def _invalidate_list_games_cache() -> None:
    _LIST_GAMES_CACHE["expires_at"] = 0.0
    _LIST_GAMES_CACHE["games"] = None


@app.route("/list_games", methods=["GET"])
def list_games():
    """List all saved games sorted newest first. Cached for 30s to avoid repeated disk scans."""
    try:
        now = time.time()
        cached = _LIST_GAMES_CACHE["games"]
        if cached is not None and now < _LIST_GAMES_CACHE["expires_at"]:
            return jsonify({"games": cached})

        games = list_all_games()
        _LIST_GAMES_CACHE["games"] = games
        _LIST_GAMES_CACHE["expires_at"] = now + _LIST_GAMES_TTL_S
        return jsonify({"games": games})
    except Exception as e:
        app.logger.error(f"Error in list_games: {str(e)}")
        return jsonify({"error": "Failed to list games"}), 500


@app.route('/play_game/<game_id>', methods=['GET'])
def play_game(game_id):
    """Serve a game's HTML file with a Content Security Policy header."""
    try:
        game_id = sanitize_game_id(game_id)
        path = game_html_path(game_id)
        if not os.path.exists(path):
            return "Game not found", 404

        response = flask.make_response(send_file(path))
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
    except Exception as e:
        app.logger.error(f"Error in play_game: {str(e)}")
        return "Error loading game", 500


if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
