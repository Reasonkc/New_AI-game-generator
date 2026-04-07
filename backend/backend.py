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
        
        if not prompt or len(prompt.strip()) == 0:
            return jsonify({"error": "Prompt cannot be empty"}), 400
        
        query = f"""You are a game design assistant. The user will give you a short description of a game idea.
Your task is to enhance and refine this prompt into a detailed game concept suitable for creating a PhaserJS game.

Make the game concept:
- Clear and specific
- Implementable in PhaserJS
- Fun and engaging
- Not too complex for a single HTML file
- Include specific mechanics, controls, and objectives
- Donot include music and particle emitters.

Original prompt: {prompt}

Generate a refined game concept with all the necessary details."""
        
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents= query
        )
        
        response_text = response.text
        
        parsed_data = {
            "title": "AI Generated Game",
            "description": response_text,
            "genre": "Action",
            "game_mechanics": ["movement", "collision"],
            "visual_style": "Simple geometric shapes",
            "controls": "Arrow keys or WASD",
            "objectives": "Complete the game objectives"
            
        }
        
        return jsonify(parsed_data)
        
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

        claude_prompt = f"""Create a complete, fully functional HTML file for a PhaserJS game.

GAME CONCEPT:
Title: {title}
Description: {description}
Genre: {genre}
Game Mechanics: {mechanics}
Visual Style: {visual_style}
Controls: {controls}
Objectives: {objectives}

MANDATORY TEXTURE CREATION PATTERN:
You MUST create all textures in the preload() method using EXACTLY this pattern:

    preload() {{
        // Create a player texture
        const gfx = this.make.graphics({{ add: false }});
        gfx.fillStyle(0xff0000);
        gfx.fillRect(0, 0, 32, 32);
        gfx.generateTexture('player', 32, 32);
        gfx.destroy();

        // Create an enemy texture
        const gfx2 = this.make.graphics({{ add: false }});
        gfx2.fillStyle(0x00ff00);
        gfx2.fillCircle(16, 16, 16);
        gfx2.generateTexture('enemy', 32, 32);
        gfx2.destroy();
    }}

    create() {{
        // Now use the textures by their string key
        this.player = this.physics.add.sprite(400, 300, 'player');
        this.enemy = this.physics.add.sprite(200, 200, 'enemy');
    }}

CRITICAL RULES:
1. ALWAYS use this.make.graphics({{ add: false }}) to create textures — NEVER this.add.graphics()
2. ALWAYS call gfx.generateTexture('keyName', width, height) with a STRING key
3. ALWAYS call gfx.destroy() after generating the texture
4. ALWAYS reference textures by their string key: this.physics.add.sprite(x, y, 'keyName')
5. NEVER do sprite.setTexture(graphics.generateTexture()) — this is BROKEN
6. NEVER use this.add.sprite() without a valid texture key — it will show a black screen
7. Create ALL textures in preload() BEFORE using them in create()

GAME STRUCTURE — Use exactly ONE scene with preload/create/update:

    class GameScene extends Phaser.Scene {{
        constructor() {{ super({{ key: 'GameScene' }}); }}
        preload() {{ /* generate ALL textures here */ }}
        create() {{ /* set up game objects, physics, input */ }}
        update() {{ /* game loop logic */ }}
    }}

    const config = {{
        type: Phaser.AUTO,
        width: 800,
        height: 600,
        backgroundColor: '#2d2d2d',
        physics: {{
            default: 'arcade',
            arcade: {{ gravity: {{ y: 0 }}, debug: false }}
        }},
        scene: [GameScene]
    }};

    const game = new Phaser.Game(config);

REQUIRED FEATURES:
- Smooth keyboard controls (arrow keys or WASD) using this.input.keyboard.createCursorKeys()
- Arcade physics with proper collision detection
- Score display using this.add.text() — update in the update() loop
- Health/lives system with game over condition
- Restart functionality (this.scene.restart())
- All visual elements drawn with fillRect, fillCircle, fillTriangle ONLY
- DO NOT use fillStar, fillHexagon, fillPolygon, or any non-standard Graphics methods
- DO NOT use external images, audio, or any URLs except the Phaser CDN
- DO NOT add music or particle emitters

TECHNICAL SPECS:
- Load Phaser from: https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js
- Canvas: 800x600 pixels
- Include proper HTML DOCTYPE, head, body tags
- Game must be immediately playable with ZERO JavaScript errors
- Game must show visible sprites on screen — NO blank/black screens

Return ONLY the complete HTML code. No explanations, no markdown."""

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=20000,
            temperature=0.7,
            messages=[{
                "role": "user", 
                "content": claude_prompt
            }]
        )
        
        game_html = extract_html_from_response(response.content[0].text)
        print(game_html)
        
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

CRITICAL RULES:
1. Return the COMPLETE updated HTML file — do not omit any sections
2. All textures MUST be created in preload() using: this.make.graphics({{ add: false }}), then .generateTexture('key', w, h), then .destroy()
3. Sprites MUST reference textures by string key: this.physics.add.sprite(x, y, 'key')
4. NEVER do sprite.setTexture(graphics.generateTexture()) — this causes black screens
5. Only use valid Graphics methods: fillRect, fillCircle, fillTriangle, strokeRect, strokeCircle, fillStyle, lineStyle
6. DO NOT use fillStar, fillHexagon, fillPolygon, or any non-standard methods
7. DO NOT add external images, audio files, or music
8. The game MUST have zero JavaScript errors and show visible sprites

Return ONLY the complete updated HTML file. No explanations, no markdown."""

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=32000,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": claude_prompt
            }]
        )
        
        updated_html = extract_html_from_response(response.content[0].text)
        
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