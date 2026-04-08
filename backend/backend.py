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

        claude_prompt = f"""Create a complete, polished, visually impressive HTML file for a PhaserJS game.

GAME CONCEPT:
Title: {title}
Description: {description}
Genre: {genre}
Game Mechanics: {mechanics}
Visual Style: {visual_style}
Controls: {controls}
Objectives: {objectives}

ASSET STRATEGY — You have TWO options for each sprite. Use whichever produces the best visuals:

OPTION A — Load free sprite images from the web in preload():
    preload() {{
        // Example: load sprites from open-source game assets
        this.load.image('player', 'https://labs.phaser.io/assets/sprites/phaser-dude.png');
        this.load.image('star', 'https://labs.phaser.io/assets/sprites/star.png');
        this.load.image('bomb', 'https://labs.phaser.io/assets/sprites/bomb.png');
        this.load.image('platform', 'https://labs.phaser.io/assets/sprites/platform.png');
        this.load.spritesheet('dude', 'https://labs.phaser.io/assets/sprites/dude.png', {{ frameWidth: 32, frameHeight: 48 }});
    }}

OPTION B — Generate detailed textures programmatically:
    preload() {{
        const gfx = this.make.graphics({{ add: false }});
        // Layer multiple shapes for detailed characters
        gfx.fillStyle(0x3366ff);
        gfx.fillCircle(16, 10, 10);       // head
        gfx.fillStyle(0x2255cc);
        gfx.fillRect(8, 18, 16, 20);      // body
        gfx.fillStyle(0x3366ff);
        gfx.fillRect(4, 22, 8, 14);       // left arm
        gfx.fillRect(20, 22, 8, 14);      // right arm
        gfx.fillStyle(0x1a1a1a);
        gfx.fillRect(10, 38, 5, 10);      // left leg
        gfx.fillRect(17, 38, 5, 10);      // right leg
        gfx.fillStyle(0xffffff);
        gfx.fillCircle(13, 8, 2);         // left eye
        gfx.fillCircle(19, 8, 2);         // right eye
        gfx.generateTexture('player', 32, 48);
        gfx.destroy();
    }}

PREFERRED APPROACH: Use OPTION A with assets from https://labs.phaser.io/assets/ whenever possible — these are free, reliable, and look professional. Fall back to OPTION B for custom elements.

AVAILABLE FREE ASSETS from Phaser Labs (use these URLs directly):
- Sprites: https://labs.phaser.io/assets/sprites/ (phaser-dude.png, star.png, bomb.png, diamond.png, mushroom.png, coin.png)
- Backgrounds: https://labs.phaser.io/assets/skies/ (space3.png, sky1.png, underwater1.png)
- Platforms: https://labs.phaser.io/assets/sprites/platform.png
- Spritesheets: https://labs.phaser.io/assets/sprites/dude.png (frameWidth: 32, frameHeight: 48)
- Particles: https://labs.phaser.io/assets/particles/ (red.png, blue.png)

CRITICAL TEXTURE RULES (for Option B only):
1. ALWAYS use this.make.graphics({{ add: false }})
2. ALWAYS call gfx.generateTexture('key', width, height) with a STRING key
3. ALWAYS call gfx.destroy() after generating
4. NEVER do sprite.setTexture(graphics.generateTexture()) — this is BROKEN

VISUAL QUALITY REQUIREMENTS:
- Create a visually rich game — use backgrounds, multiple layers, color gradients
- Use multiple layered shapes to create detailed characters (head, body, limbs, eyes)
- Add visual effects: screen shake on hits, flash on damage, tween animations on pickups
- Smooth camera following the player if the world is larger than the screen
- Parallax scrolling backgrounds when appropriate
- Polished UI: styled score display, animated health bar, attractive game over screen with stats
- Add sprite animations using this.anims.create() when using spritesheets

GAME STRUCTURE:
    class GameScene extends Phaser.Scene {{
        constructor() {{ super({{ key: 'GameScene' }}); }}
        preload() {{ /* load assets or generate textures */ }}
        create() {{ /* set up game objects, physics, input, animations */ }}
        update() {{ /* game loop logic */ }}
    }}

    const config = {{
        type: Phaser.AUTO,
        width: 800,
        height: 600,
        physics: {{
            default: 'arcade',
            arcade: {{ gravity: {{ y: 300 }}, debug: false }}
        }},
        scene: [GameScene]
    }};

REQUIRED FEATURES:
- Smooth keyboard controls (arrow keys or WASD)
- Arcade physics with proper collision detection
- Score display and health/lives system
- Game over screen with restart functionality
- At least 3 different types of game objects (player, enemies, collectibles)
- Progressive difficulty (gets harder over time)
- Visual feedback on all interactions (collect, damage, game over)

TECHNICAL SPECS:
- Load Phaser from: https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js
- Canvas: 800x600 pixels
- Include proper HTML DOCTYPE, head, body tags
- ZERO JavaScript errors — test every function call mentally before writing it
- Game must render visible sprites immediately — NO blank screens

Return ONLY the complete HTML code. No explanations, no markdown."""

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

TECHNICAL SETUP:
- Load Three.js from CDN: https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js
- Full HTML file with DOCTYPE, head, body
- Canvas fills the browser window (width: 100vw, height: 100vh)
- Use requestAnimationFrame for the game loop

3D SCENE REQUIREMENTS:
- Create a proper Three.js scene with PerspectiveCamera and WebGLRenderer
- Add lighting: ambient light + directional light with shadows enabled
- Use a ground plane with a grid or textured material
- Create 3D objects using Three.js geometries:
    * THREE.BoxGeometry for cars, buildings, obstacles
    * THREE.CylinderGeometry for wheels, poles
    * THREE.PlaneGeometry for ground, walls
    * THREE.SphereGeometry for balls, decorative elements
- Use THREE.MeshStandardMaterial or THREE.MeshPhongMaterial for realistic shading
- Group related meshes using THREE.Group (e.g., car body + wheels = one group)
- Add colors and materials that look good — not just white boxes

CAMERA:
- Third-person camera following the player object
- Smooth camera interpolation using lerp
- Camera should orbit slightly based on movement direction

CONTROLS:
- Arrow keys or WASD for movement
- Smooth acceleration and deceleration (not instant teleport)
- Realistic turning/steering for vehicles
- Event listeners for keydown/keyup to track pressed keys

PHYSICS (simple custom — do NOT import external physics libraries):
- Implement basic collision detection using bounding boxes (object.position distance checks)
- Simple velocity and acceleration model
- Gravity only if needed (jumping games)
- Wall/boundary collision — prevent going through objects

REQUIRED GAME ELEMENTS:
- A player-controlled 3D object (car, character, etc.)
- At least 5 obstacles or interactive objects in the scene
- A scoring or objective system (park in spot, reach destination, collect items)
- Timer or move counter
- HUD overlay using HTML div positioned over the canvas (position: absolute)
- Win/lose conditions
- Restart functionality

VISUAL QUALITY:
- Ground with visible grid lines or color pattern
- Shadows enabled (renderer.shadowMap.enabled = true)
- Multiple colored objects — not a monochrome scene
- Smooth 60fps rendering
- Environment objects (trees as green cylinders+spheres, buildings as boxes)

EXAMPLE CAR STRUCTURE:
    function createCar(color) {{
        const car = new THREE.Group();
        // Body
        const bodyGeo = new THREE.BoxGeometry(2, 0.5, 4);
        const bodyMat = new THREE.MeshStandardMaterial({{ color: color }});
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = 0.5;
        body.castShadow = true;
        car.add(body);
        // Cabin
        const cabinGeo = new THREE.BoxGeometry(1.5, 0.5, 2);
        const cabinMat = new THREE.MeshStandardMaterial({{ color: 0x88ccff }});
        const cabin = new THREE.Mesh(cabinGeo, cabinMat);
        cabin.position.set(0, 1, -0.2);
        cabin.castShadow = true;
        car.add(cabin);
        // Wheels
        const wheelGeo = new THREE.CylinderGeometry(0.3, 0.3, 0.3, 16);
        const wheelMat = new THREE.MeshStandardMaterial({{ color: 0x333333 }});
        [[-1, 0.3, 1.2], [1, 0.3, 1.2], [-1, 0.3, -1.2], [1, 0.3, -1.2]].forEach(pos => {{
            const wheel = new THREE.Mesh(wheelGeo, wheelMat);
            wheel.rotation.z = Math.PI / 2;
            wheel.position.set(...pos);
            car.add(wheel);
        }});
        return car;
    }}

CRITICAL RULES:
- ZERO JavaScript errors — the game MUST work on first load
- Do NOT import modules (no import/export) — use vanilla script tags
- Do NOT use OrbitControls or any external Three.js addons
- All 3D objects must be visible — set proper positions, camera must see the scene
- The renderer must be appended to document.body
- Include window resize handler to keep aspect ratio correct

Return ONLY the complete HTML code. No explanations, no markdown."""

        # Use streaming to avoid SDK timeout on large responses
        result_text = ""
        with claude_client.messages.stream(
            model="claude-opus-4-20250514",
            max_tokens=20000,
            temperature=0.7,
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
            model="claude-opus-4-20250514",
            max_tokens=32000,
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