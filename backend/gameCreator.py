from google import genai
import json
from pydantic import BaseModel
client = genai.Client(api_key="AIzaSyAFSjqpFOK2aG1jilF5RciOpjNbQYNi4cE")

class responseBase(BaseModel):
    title: str
    description: str
    genre: str
    required_assets: list[str]
    game_logic: str
    instructions: str

class plan(BaseModel):
    sprite_textures: list[str]
    logic_functions: list[str]

class bootscene(BaseModel):
    code : str
    textures: list[str]

class scene(BaseModel):
    code : str


def create_json(prompt):
    client = genai.Client(api_key="AIzaSyAFSjqpFOK2aG1jilF5RciOpjNbQYNi4cE")
    query = f"""You are a game design assistant. The user will give you a short description of a game idea in natural language.
            Your task is to generate a structured JSON object that represents this game concept. Donot add sound assets or music to the game.
            The idea is {prompt}."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
    config={
        'response_mime_type': 'application/json',
        'response_schema': responseBase,
    },
    )
    parsed_data = json.loads(response.text)
    return parsed_data




def plan_generator(config):
    query = f"""Create a plan for a simple game using Phaser 3. The game description is:{config}. The plan should include:
    1. A list of name of sprite textures to be used in the game.
    2. A list of logic functions that will be used in the game. make as many as possible which make the game better and specified in the description."""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=query,
        config={
            'response_mime_type': 'application/json',
            'response_schema': plan,
        },
    )
    parsed_data = json.loads(response.text)
    return parsed_data

def sprite_generator(sprite_textures):
    query = f"""Write a BootScene class that extends phasor.Scene. The class should load
      the following sprite textures: {sprite_textures}.

      The class should generate all textures using only shapes and colors. Do not use any images or external assets.
      The class should include a create method to start gamescene after loading the textures.
      The class should also include a preload method that loads the generated textures.
      Also respond with names of sprited you generated in the code.
      Donot write import export statements.
      Donot use music and particle emitter.
      For Preloader, use this format:
      preload() {{
                // Display loading text
                this.add.text(
                    this.cameras.main.width / 2,
                    this.cameras.main.height / 2,
                    'Loading game...',
                    {{ font: '24px Arial', fill: '#ffffff' }}
                ).setOrigin(0.5);

                // Generate all textures programmatically
                this.generateTextures();
            }}

            generateTextures() {{
                // Background with stars
                this.generateStarfieldTexture();

                // Player ship
                this.generatePlayerTexture();
            }}

            generateStarfieldTexture() {{
                const graphics = this.make.graphics({{ x: 0, y: 0, add: false }});
                graphics.fillStyle(0x000000);
                graphics.fillRect(0, 0, 800, 600);

                // Add some stars
                graphics.fillStyle(0xFFFFFF);
                for (let i = 0; i < 200; i++) {{
                    const x = Phaser.Math.Between(0, 800);
                    const y = Phaser.Math.Between(0, 600);
                    const size = Phaser.Math.Between(1, 3);
                    graphics.fillRect(x, y, size, size);
                }}

                // Add some bigger stars with glow
                graphics.fillStyle(0x00AAFF);
                for (let i = 0; i < 40; i++) {{
                    const x = Phaser.Math.Between(0, 800);
                    const y = Phaser.Math.Between(0, 600);
                    const size = Phaser.Math.Between(2, 4);
                    graphics.fillRect(x, y, size, size);
                }}

                graphics.generateTexture('background', 800, 600);
            }}
            generatePlayerTexture(){{
                const graphics = this.make.graphics({{x: 0, y: 0, add: false }});
                
                // Ship body
                graphics.fillStyle(0x4444FF);
                graphics.fillRect(15, 0, 20, 40);
                
                // Wings
                graphics.fillStyle(0x2222AA);
                graphics.fillTriangle(0, 30, 15, 15, 15, 40);
                graphics.fillTriangle(50, 30, 35, 15, 35, 40);
                
                // Engine
                graphics.fillStyle(0xFF8800);
                graphics.fillRect(20, 40, 10, 5);
                
                graphics.generateTexture('player', 50, 45);
            }}
      """
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=query,
        config={
            'response_mime_type': 'application/json',
            'response_schema': bootscene,
        },
    )
    parsed_data = json.loads(response.text)
    return parsed_data

def game_logic_generator(sprite_textures,logic_functions, config):
    query = f"""Write a GameScene class that extends phasor.Scene. 
    The class should implement the game logic for the game described in the config: {config} 
    and include all logic functions {logic_functions}. 
    Donot leave any function as comments.
    The sprites are already loaded in bootScene ao no need to load them, just use these sprite and texture names: {sprite_textures} . 
    The class should include methods for handling player input, updating the game state, and rendering the game. 
    The class should also include methods for handling collisions and interactions between game objects.
    Also add config for the game after end of GameScene Class. and create a game instance using the config.
    If there is a jump function, focus properly on touching the ground and jumping.
    Ensure proper game restart function.
    DONOT add sound effect or music to the game.
    DONOT add a preloader to the game.
    donot write import export statements."""
    response = client.models.generate_content(
        model="gemini-1.5-pro",
        contents=query, 
        config={
            'response_mime_type': 'application/json',
            'response_schema': scene,
        },
    )
    parsed_data = json.loads(response.text)
    return parsed_data

def validate_generated_code(code, required_functions):
    """Validate that all required functions are implemented in the generated code."""
    # Basic validation that all required functions exist
    missing_functions = []
    for func in required_functions:
        if func not in code:
            missing_functions.append(func)
    
    if missing_functions:
        raise ValueError(f"Missing required functions: {', '.join(missing_functions)}")
    
    # Check for common errors
    common_errors = [
        "TODO", 
        "//", 
        "/* */", 
        "function()", 
        "undefined"
    ]
    
    for error in common_errors:
        if error in code:
            raise ValueError(f"Detected potential incomplete code: {error}")
    
    return True

def create_game(config):
    # Generate the game plan
    plan = plan_generator(config)
    
    # Validate the plan
    if not plan["sprite_textures"] or not plan["logic_functions"]:
        raise ValueError("Game plan missing required elements")
    
    # Generate boot scene with sprites
    sprite_textures = ', '.join(plan["sprite_textures"])
    bootscenecode = sprite_generator(sprite_textures)
    
    # Validate bootscene code
    if not bootscenecode["code"] or not bootscenecode["textures"]:
        raise ValueError("Boot scene generation failed")
    
    # Make sure all required textures are included
    missing_textures = [texture for texture in plan["sprite_textures"] 
                       if texture not in ' '.join(bootscenecode["textures"])]
    if missing_textures:
        print(f"Warning: Some textures may be missing: {missing_textures}")
    
    # Generate game logic
    sprite_names = ', '.join(bootscenecode['textures'])
    game_logic_result = game_logic_generator(sprite_names, plan["logic_functions"], config)
    game_logic = game_logic_result["code"]
    
    # Validate game logic
    try:
        validate_generated_code(game_logic, plan["logic_functions"])
    except ValueError as e:
        print(f"Warning: Game logic validation issue: {e}")
        # Here you could implement retry logic
    
    # Combine and format the game
    game_logic = game_logic.replace("scene: [GameScene]", "scene: [BootScene, GameScene]")
    game_logic = game_logic.replace("scene: GameScene", "scene: [BootScene, GameScene]")
    
    # Create the final HTML
    html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config['title']}</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/phaser/3.55.2/phaser.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #000;
            }}
            canvas {{
                display: block;
            }}
        </style>
    </head>
    <body>
        <script>
        {bootscenecode['code']}
        {game_logic}
        </script>
    </body>
    </html>
    """
    
    # Save the game
    with open(f"{config['title'].replace(' ', '_').lower()}.html", "w") as file:
        file.write(html)
    
    print(f"Game '{config['title']}' created successfully!")
    return html

if __name__ == "__main__":
    config = create_json("A simple game where a player controls a character that can jump and collect coins. The game should have a simple background and a few obstacles.")
    print(config)
    create_game(config)