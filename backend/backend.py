from google import genai
import json
import flask
from flask import request, jsonify, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import anthropic
import os
import uuid
from datetime import datetime
import re
from dotenv import load_dotenv
load_dotenv()
# client = genai.Client()



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
app = flask.Flask(__name__)
CORS(app)

# Initialize rate limiter to prevent API abuse and control costs
# Limits: enhance_prompt (10/hr), generate_game (5/hr), update_game (5/hr)
# Tracks by IP address; resets on server restart (in-memory storage)
limiter =Limiter(
    app=app,
    key_func = get_remote_address,
    default_limits=["150 per day", "35 per hour"],
    storage_uri="memory://"
)

if not GEMINI_API_KEY or not CLAUDE_API_KEY:
    raise ValueError("API keys must be set as environment variables")


claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Create games directory if it doesn't exist
GAMES_DIR = "games"
if not os.path.exists(GAMES_DIR):
    os.makedirs(GAMES_DIR)

def sanitize_game_id(game_id):
    """Validate game_id to prevent path traversal attacks"""
    if not re.match(r'^[a-f0-9-]{36}$', game_id):
        raise ValueError("Invalid game ID format")
    return game_id

def extract_html_from_response(text):
    """Extract HTML code from Claude's response, removing markdown code blocks"""
    original_length = len(text)
    
    # Remove markdown code blocks if present
    text = re.sub(r'^```html\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```$', '', text, flags=re.MULTILINE)
    
    # Clean up any remaining markdown artifacts
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    
    cleaned_text = text.strip()
    
    # Log for debugging
    app.logger.info(f"Original response length: {original_length}")
    app.logger.info(f"Cleaned HTML length: {len(cleaned_text)}")
    
    # Check if HTML seems complete
    if not cleaned_text.lower().endswith('</html>'):
        app.logger.warning("HTML response appears to be truncated - missing closing </html> tag")
        
    # Check for common truncation indicators
    if cleaned_text.endswith('...'):
        app.logger.warning("Response appears to be truncated (ends with ...)")
    
    return cleaned_text

@app.route('/enhance_prompt', methods=['POST'])
@limiter.limit("10 per hour")
def enhance_prompt():
    """Use Gemini to refine and enhance the user's game prompt"""
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({"error": "Missing 'prompt' in request"}), 400

        prompt = data['prompt']
        engine = data.get('engine', 'phaser')

        if not prompt or len(prompt.strip()) == 0:
            return jsonify({"error": "Prompt cannot be empty"}), 400

        if engine == "threejs":
            engine_context = """The game will be built as a 3D browser game using Three.js.
Think in terms of 3D space: camera angles, lighting, 3D models made from basic geometries (boxes, cylinders, spheres).
Suitable genres: driving, parking, simulation, racing, flight, 3D exploration, tower defense with 3D view.
Controls should consider 3D movement (forward/backward, turning, camera rotation)."""
        else:
            engine_context = """The game will be built as a 2D browser game using PhaserJS.
Think in terms of 2D space: side-scrolling, top-down, or fixed-screen views.
Suitable genres: platformers, shooters, puzzles, arcade, match-3, endless runners.
All sprites will be created programmatically or loaded from free sprite libraries."""

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

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=query
        )

        response_text = response.text

        # Extract title from response if present
        title = "AI Generated Game"
        genre = "Action"
        visual_style = "Detailed and polished"
        controls = "Arrow keys or WASD"
        objectives = "Complete the game objectives"

        for line in response_text.split('\n'):
            line_clean = line.strip().replace('**', '')
            if line_clean.upper().startswith('TITLE:'):
                title = line_clean.split(':', 1)[1].strip()
            elif line_clean.upper().startswith('GENRE:'):
                genre = line_clean.split(':', 1)[1].strip()
            elif line_clean.upper().startswith('VISUAL STYLE:'):
                visual_style = line_clean.split(':', 1)[1].strip()
            elif line_clean.upper().startswith('CONTROLS:'):
                controls = line_clean.split(':', 1)[1].strip()
            elif line_clean.upper().startswith('OBJECTIVES:'):
                objectives = line_clean.split(':', 1)[1].strip()

        return jsonify({
            "title": title,
            "description": response_text,
            "genre": genre,
            "game_mechanics": ["movement", "collision", "scoring"],
            "visual_style": visual_style,
            "controls": controls,
            "objectives": objectives
        })

    except Exception as e:
        app.logger.error(f"Error in enhance_prompt: {str(e)}")
        return jsonify({"error": "Failed to enhance prompt"}), 500

@app.route('/generate_game', methods=['POST'])
@limiter.limit("5 per hour")
def generate_game():
    """Use Claude to generate PhaserJS game code based on enhanced prompt"""
    try:
        data = request.get_json()
        if not data or 'enhanced_prompt' not in data:
            return jsonify({"error": "Missing 'enhanced_prompt' in request"}), 400
            
        enhanced_prompt = data['enhanced_prompt']
        engine = data.get('engine', 'phaser')

        # Handle both string and object types for enhanced_prompt
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

        claude_prompt = f"""Build a complete, polished, PLAYABLE PhaserJS game in a single HTML file.

CONCEPT: {title} ({genre})
{description}
Mechanics: {mechanics}
Controls: {controls}
Objectives: {objectives}
Visual Style: {visual_style}

Before writing code, think carefully about what makes THIS specific game genre fun:
- If it's a maze/arcade game (Pacman-style): grid-based movement, wall collision, dots to collect, enemies with simple AI patrol or chase logic, win condition when all dots collected
- If it's a platformer: gravity, jumping, platforms to land on, enemies that walk and can be defeated, collectibles, exit/flag
- If it's a shooter: projectile spawning + group, enemy waves, health system, power-ups, game over on death
- If it's a puzzle: turn-based logic, click/drag interactions, level progression, move counter
- If it's an endless runner: auto-scrolling world, jump/duck mechanics, obstacles, increasing speed

Match the mechanics to the genre — do NOT generate a generic shooter if the user asked for a maze game.

SETUP:
- Load Phaser 3.80.1: https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js
- Canvas 800x600, Phaser.AUTO, arcade physics (gravity set appropriately for the genre)

TEXTURE RULES (critical — get this wrong and the game is broken):
For custom sprites, use this EXACT pattern in preload():
  const gfx = this.make.graphics({{ add: false }});
  gfx.fillStyle(0xffff00); gfx.fillCircle(16, 16, 14);
  gfx.generateTexture('player', 32, 32); gfx.destroy();
Then use by string key: this.player = this.physics.add.sprite(x, y, 'player');

NEVER: this.add.graphics() for textures. NEVER: sprite.setTexture(gfx.generateTexture()). NEVER: fillStar, fillHexagon, fillPolygon.

You may also load free sprites from labs.phaser.io (phaser-dude.png, star.png, bomb.png, diamond.png, coin.png, platform.png) or backgrounds from labs.phaser.io/assets/skies/.

REQUIRED FEATURES:
- Single GameScene class with preload(), create(), and update() methods
- Responsive keyboard input (this.cursors = this.input.keyboard.createCursorKeys())
- A functional game loop matching the genre (not just random sprites floating around)
- Win/lose conditions with clear end states
- Score display (this.add.text()) updated in the update() loop
- Game over screen with restart capability (this.scene.restart() or keyboard press to restart)
- At least 3 distinct object types that interact (player, enemies/hazards, collectibles/goals)
- Collision detection between appropriate pairs (this.physics.add.collider and overlap)
- Visual feedback on interactions (tweens on collect, color flashes on damage)

Double-check before outputting:
1. Does the game mechanic match what the user asked for?
2. Will it show visible sprites on load (not a black screen)?
3. Are there any undefined functions or missing texture keys?
4. Is there a clear way to win AND a clear way to lose?

OUTPUT: Complete HTML only — DOCTYPE, head, body. No explanations. No markdown fences. Zero JavaScript errors."""

        # Three.js prompt for 3D games
        if engine == "threejs":
            claude_prompt = f"""Create a complete, polished 3D game in a single HTML file using Three.js.

GAME CONCEPT:
Title: {title}
Description: {description}
Genre: {genre}
Game Mechanics: {mechanics}
Controls: {controls}
Objectives: {objectives}

SETUP:
- Load Three.js r128: https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js
- Canvas fills window (100vw/100vh), appended to document.body
- requestAnimationFrame game loop, window resize handler

SCENE:
- PerspectiveCamera + WebGLRenderer with shadowMap.enabled = true
- Ambient + directional light (castShadow = true)
- Ground plane with grid/color pattern
- Use BoxGeometry, CylinderGeometry, SphereGeometry, PlaneGeometry
- MeshStandardMaterial with varied colors (no monochrome)
- Group related meshes (THREE.Group for cars: body + cabin + 4 wheels)

GAMEPLAY:
- Third-person camera following player, smooth lerp
- Keyboard input via keydown/keyup listeners (WASD or arrows)
- Smooth acceleration/deceleration — NOT instant teleport
- Realistic turning for vehicles (steer angle affects heading)
- Custom physics: bounding-box collision, velocity model, boundary checks
- NO external physics libs, NO import/export, NO OrbitControls

REQUIRED:
- Player-controlled 3D object
- 5+ obstacles/interactive objects
- HUD overlay (HTML div, position: absolute) — score, timer, objectives
- Win/lose conditions + restart functionality
- Environment props (trees, buildings) for visual richness

Example car pattern:
  const car = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(2, 0.5, 4), new THREE.MeshStandardMaterial({{color: 0xff0000}}));
  body.castShadow = true; car.add(body);
  // ... add cabin + 4 wheels (CylinderGeometry rotated on z by PI/2)

OUTPUT: Complete HTML only — DOCTYPE, head, body. No explanations, no markdown fences. Zero JS errors. Visible 3D scene on load."""

        # Use streaming to avoid SDK timeout on large responses
        result_text = ""
        with claude_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            temperature=0.6,
            messages=[{
                "role": "user",
                "content": claude_prompt
            }]
        ) as stream:
            for text in stream.text_stream:
                result_text += text

        game_html = extract_html_from_response(result_text)
        
        # Generate unique game ID and save the game
        game_id = str(uuid.uuid4())
        game_folder = os.path.join(GAMES_DIR, game_id)
        os.makedirs(game_folder, exist_ok=True)
        
        # Save the HTML file
        game_path = os.path.join(game_folder, "index.html")
        with open(game_path, "w", encoding="utf-8") as file:
            file.write(game_html)
        
        # Save metadata using local variables extracted from the if/else block
        metadata = {
            "id": game_id,
            "title": title,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "genre": genre,
            "file_path": game_path
        }

        metadata_path = os.path.join(game_folder, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        return jsonify({
            "game_id": game_id,
            "title": title,
            "status": "created",
            "play_url": f"/play_game/{game_id}"
        })
        
    except Exception as e:
        app.logger.error(f"Error in generate_game: {str(e)}")
        return jsonify({"error": "Failed to generate game"}), 500

@app.route('/update_game', methods=['POST'])
@limiter.limit("5 per hour")
def update_game():
    """Update an existing game based on feedback"""
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

        # Use streaming to avoid SDK timeout on large requests
        result_text = ""
        with claude_client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": claude_prompt
            }]
        ) as stream:
            for text in stream.text_stream:
                result_text += text

        updated_html = extract_html_from_response(result_text)
        
        # If game_id is provided, update the saved file
        if game_id:
            try:
                game_id = sanitize_game_id(game_id)
                game_folder = os.path.join(GAMES_DIR, game_id)
                if os.path.exists(game_folder):
                    game_path = os.path.join(game_folder, "index.html")
                    with open(game_path, "w", encoding="utf-8") as file:
                        file.write(updated_html)
            except ValueError:
                pass  # Invalid game_id, just return the HTML without saving
        
        return jsonify({"html": updated_html})
        
    except Exception as e:
        app.logger.error(f"Error in update_game: {str(e)}")
        return jsonify({"error": "Failed to update game"}), 500

@app.route("/get_game/<game_id>", methods=["GET"])
def get_game(game_id):
    """Retrieve a saved game by ID"""
    try:
        game_id = sanitize_game_id(game_id)
        game_path = os.path.join(GAMES_DIR, game_id, "index.html")
        metadata_path = os.path.join(GAMES_DIR, game_id, "metadata.json")
        
        if not os.path.exists(game_path):
            return jsonify({"error": "Game not found"}), 404
        
        with open(game_path, "r", encoding="utf-8") as file:
            game_content = file.read()
        
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as file:
                metadata = json.load(file)
        
        return jsonify({
            "game_id": game_id,
            "html": game_content,
            "metadata": metadata
        })
        
    except ValueError:
        return jsonify({"error": "Invalid game ID"}), 400
    except Exception as e:
        app.logger.error(f"Error in get_game: {str(e)}")
        return jsonify({"error": "Failed to retrieve game"}), 500

@app.route("/list_games", methods=["GET"])
def list_games():
    """List all saved games"""
    try:
        games = []
        if os.path.exists(GAMES_DIR):
            for game_id in os.listdir(GAMES_DIR):
                try:
                    game_id = sanitize_game_id(game_id)
                    metadata_path = os.path.join(GAMES_DIR, game_id, "metadata.json")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r", encoding="utf-8") as file:
                            metadata = json.load(file)
                            games.append(metadata)
                except (ValueError, json.JSONDecodeError):
                    continue  # Skip invalid game directories
        
        # Sort by creation date, newest first
        games.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({"games": games})
        
    except Exception as e:
        app.logger.error(f"Error in list_games: {str(e)}")
        return jsonify({"error": "Failed to list games"}), 500

@app.route('/play_game/<game_id>', methods=['GET'])
def play_game(game_id):
    """Serve the game HTML directly for playing with CSP protection"""
    try:
        game_id = sanitize_game_id(game_id)
        game_path = os.path.join(GAMES_DIR, game_id, "index.html")
        
        if not os.path.exists(game_path):
            return "Game not found", 404
        
        # Create response with the file
        response = flask.make_response(send_file(game_path))
        
        # Add Content Security Policy header to restrict what the game can load
        # Allows: scripts from self and CDN, inline scripts/styles (needed for games)
        # Blocks: scripts from unknown domains, tracking pixels, external resources
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