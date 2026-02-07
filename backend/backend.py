from google import genai
import json
import flask
from flask import request, jsonify, send_file
from flask_cors import CORS
import anthropic
import os
import uuid
from datetime import datetime
import re
from dotenv import load_dotenv
load_dotenv()




GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
app = flask.Flask(__name__)
CORS(app)



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
            model="gemini-3-flash-preview", contents= query
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

        claude_prompt = f"""Create a complete, fully functional HTML file for a game using PhaserJS based on this detailed game concept:

GAME CONCEPT:
Title: {title}
Description: {description}
Genre: {genre}
Game Mechanics: {mechanics}
Visual Style: {visual_style}
Controls: {controls}
Objectives: {objectives}

CRITICAL REQUIREMENTS FOR A FULLY FUNCTIONAL GAME:

1. **Complete HTML Structure**: Create a self-contained HTML file with proper DOCTYPE, head, and body tags
2. **PhaserJS 3.x Integration**: Load Phaser from CDN: https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js
3. **Proper Physics Engine**: Use Phaser's Arcade Physics system with proper collision detection, gravity, and realistic movement
4. **Game States Management**: Include proper game states (preload, create, update) with smooth transitions
5. **Responsive Controls**: Implement smooth, responsive keyboard controls (arrow keys/WASD) with proper input handling
6. **Visual Polish**: Create visually appealing game objects using ONLY Phaser's Graphics API with programmatically drawn sprites, shapes, colors, animations, and effects - NO external image assets
8. **Scoring System**: Implement a functional scoring system with proper UI display
9. **Game Mechanics**: 
   - Proper collision detection between all game objects
   - Smooth player movement with acceleration/deceleration
   - Enemy AI with varied behaviors and attack patterns
   - Power-ups with visual and functional effects
   - Health/lives system with proper game over conditions
10. **Performance Optimization**: Use object pooling for bullets/enemies, efficient sprite management
11. **Game Loop**: Proper game loop with pause/resume functionality
12. **UI Elements**: Score display, health bars, game over screen, restart functionality


TECHNICAL SPECIFICATIONS:
- Use Phaser 3.80.1 or later
- Canvas size: 800x600 pixels
- 60 FPS target
- Create all assets programmatically using Phaser's Graphics API - NO external image/audio files
- Clean, well-commented code structure
- No external dependencies except Phaser CDN

ASSET CREATION REQUIREMENTS:
- CREATE ALL ASSETS PROGRAMMATICALLY - No external files allowed
- Use Phaser's Graphics API to draw all sprites, backgrounds, UI elements
- Generate sounds using Web Audio API with oscillators and frequency manipulation
- Create textures using Phaser's built-in texture generation capabilities
- Use geometric shapes, gradients, and patterns for all visual elements
- All game assets must be self-contained within the HTML file

PHASER.JS FUNCTION VALIDATION:
- ONLY use valid Phaser.js 3.x functions and methods that exist in the official API
- For Graphics API, use ONLY these valid functions:
    * fillStyle(color, alpha?)
    * lineStyle(width, color, alpha?)
    * fillRect(x, y, width, height)
    * strokeRect(x, y, width, height)
    * fillCircle(x, y, radius)
    * strokeCircle(x, y, radius)
    * fillTriangle(x1, y1, x2, y2, x3, y3)
    * strokeTriangle(x1, y1, x2, y2, x3, y3)
    * fillPoints(points, closeShape=true)
    * strokePoints(points, closeShape=true)
    * (optional) fillEllipse(x, y, width, height)
    * (optional) strokeEllipse(x, y, width, height)
    * (optional) fillRoundedRect(x, y, width, height, radius)
    * (optional) strokeRoundedRect(x, y, width, height, radius)
- DO NOT use non-existent functions like fillStar, fillHexagon, or any other made-up functions
- For creating star shapes, use fillPolygon with calculated star points
- Test all function calls against the official Phaser 3 documentation
- If unsure about a function, use basic shapes like rectangles, circles, and triangles
- this.add.graphics(...).fillStyle(...).fillPolygon is not a function

GAMEPLAY QUALITY STANDARDS:
- The game must be immediately playable and engaging
- Controls must feel responsive and smooth
- Game mechanics must work flawlessly without bugs
- Visual feedback must be clear and satisfying
- Game difficulty should be balanced and fair
- Include proper win/lose conditions
- All Phaser.js functions MUST be valid and working

Return ONLY the complete HTML code with no explanations or markdown formatting. The game should be production-ready and fully functional with NO JavaScript errors."""

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
        
        # Save metadata
        metadata = {
            "id": game_id,
            "title": enhanced_prompt.get('title', 'Untitled Game'),
            "description": enhanced_prompt.get('description', ''),
            "created_at": datetime.now().isoformat(),
            "genre": enhanced_prompt.get('genre', ''),
            "file_path": game_path
        }
        
        metadata_path = os.path.join(game_folder, "metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)
        
        return jsonify({
            "game_id": game_id,
            "html": game_html,
            "title": enhanced_prompt.get('title', 'Untitled Game'),
            "file_path": game_path
        })
        
    except Exception as e:
        app.logger.error(f"Error in generate_game: {str(e)}")
        return jsonify({"error": "Failed to generate game"}), 500

@app.route('/update_game', methods=['POST'])
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

CRITICAL REQUIREMENTS:
1. ONLY use valid Phaser.js 3.x functions that exist in the official API
2. DO NOT use non-existent functions like fillStar, fillHexagon, or any made-up Graphics functions
3. CREATE ALL ASSETS PROGRAMMATICALLY - No external image or audio files allowed
4. Use Phaser's Graphics API to draw all sprites, backgrounds, UI elements
5. Generate sounds using Web Audio API with oscillators - no external audio files
6. All game content must be self-contained within the HTML file

Valid Graphics functions include: fillRect, fillCircle, fillTriangle, fillPolygon, strokeRect, strokeCircle, strokeTriangle, strokePolygon, fillStyle, lineStyle.

Keep the same PhaserJS structure but implement the requested changes. Return ONLY the complete updated HTML file with no explanations. Ensure NO JavaScript errors occur and NO external asset dependencies."""

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
    """Serve the game HTML directly for playing"""
    try:
        game_id = sanitize_game_id(game_id)
        game_path = os.path.join(GAMES_DIR, game_id, "index.html")
        
        if not os.path.exists(game_path):
            return "Game not found", 404
        
        return send_file(game_path)
        
    except ValueError:
        return "Invalid game ID", 400
    except Exception as e:
        app.logger.error(f"Error in play_game: {str(e)}")
        return f"Error loading game", 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)