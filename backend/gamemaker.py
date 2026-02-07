import anthropic
from google import genai
import json
from pydantic import BaseModel
import re
client = anthropic.Anthropic()
class responseBase(BaseModel):
    title: str
    description: str
    genre: str
    required_assets: list[str]
    game_logic: str
    instructions: str
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

def generate_game_code(config):
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=20000,
        temperature=1,
        system="You are a game developer. ",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Create a simple game in a single HTML file using Phaser 3. Donot use sprites or images in the game. 
                        Create the sprites using Phaser's built-in graphics functions and shapes to resemble the assets but donot make too much complicated just add some features only.
                    Use the following JSON object as the Phaser. Config: {config} 
                    Functions that use the Phaser scene context (this) must be correctly scoped:
                    • Either define them inside the scene object, or
                    • Call them using .call(this) or .bind(this) to ensure correct context.
                    Only provide the code and nothing else. Do not add any other text or explanation. 
                    The game code should be a single HTML file that can be run in a web browser.
                    Donot add music or sound assets to the game"""
                    }
                ]
            }
        ]
    )
    response = message.content[0].text
    print(response)
    html_content = ""
    match = re.search(r"<!DOCTYPE html>.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"<html>.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"<html lang=\"en\">.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if match:
        html_content = match.group()
        print(html_content)
    return html_content

def update_game(feedback,code):
    message = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=20000,
        temperature=1,
        system="You are a game developer. ",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""update the game code with the following feedback: {feedback}. The game code is {code}.
                        Only provide the code and nothing else. Do not add any other text or explanation.
                        The game code should be a single HTML file that can be run in a web browser."""
                    }
                ]
            }
        ]
    )
    response = message.content[0].text
    print(response)
    html_content = ""
    match = re.search(r"<!DOCTYPE html>.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"<html>.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if not match:
        match = re.search(r"<html lang=\"en\">.*?</html>", response, re.DOTALL | re.IGNORECASE)
    if match:
        html_content = match.group()
        print(html_content)
    return html_content


if __name__ == "__main__":
    prompt = "A mario type platformer game but with mouse as main character. Cheese platform and apple powerups and cat and dog enemies."
    json_config = create_json(prompt)
    print(json_config)
    game_code = generate_game_code(json_config)
    with open("game.html", "w") as f:
        f.write(game_code)
