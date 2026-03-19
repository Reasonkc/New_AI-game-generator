"""Prompt templates for AI API calls."""


def build_enhance_prompt(user_prompt: str) -> str:
    """Build the Gemini prompt for enhancing a user's game idea."""
    return f"""You are a game design assistant. The user will give you a short description of a game idea.
Your task is to enhance and refine this prompt into a detailed game concept suitable for creating a PhaserJS game.

Make the game concept:
- Clear and specific
- Implementable in PhaserJS
- Fun and engaging
- Not too complex for a single HTML file
- Include specific mechanics, controls, and objectives
- Donot include music and particle emitters.

Original prompt: {user_prompt}

Generate a refined game concept with all the necessary details."""


def build_generate_prompt(title: str, description: str, genre: str,
                          mechanics: str, visual_style: str, controls: str,
                          objectives: str) -> str:
    """Build the Claude prompt for generating a PhaserJS game."""
    return f"""Create a complete, fully functional HTML file for a game using PhaserJS based on this detailed game concept:

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
- DO NOT use non-existent functions like fillStar, fillHexagon, or any other made-up functions
- For creating star shapes, use fillPolygon with calculated star points
- If unsure about a function, use basic shapes like rectangles, circles, and triangles

GAMEPLAY QUALITY STANDARDS:
- The game must be immediately playable and engaging
- Controls must feel responsive and smooth
- Game mechanics must work flawlessly without bugs
- Visual feedback must be clear and satisfying
- Game difficulty should be balanced and fair
- Include proper win/lose conditions
- All Phaser.js functions MUST be valid and working

Return ONLY the complete HTML code with no explanations or markdown formatting. The game should be production-ready and fully functional with NO JavaScript errors."""


def build_update_prompt(current_html: str, feedback: str) -> str:
    """Build the Claude prompt for updating an existing game."""
    return f"""Here is the current HTML game code:

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
