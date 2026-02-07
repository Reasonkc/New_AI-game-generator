# AI Game Generator Backend

Flask-based API server for the AI Game Generator. Uses Gemini API for prompt enhancement and Claude API for game generation.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Add your API keys to .env file
```

3. Run the server:
```bash
python backend.py
```

## API Endpoints

- `POST /enhance-prompt` - Enhance user prompt with Gemini AI
- `POST /generate-game` - Generate game with Claude AI 
- `POST /update-game` - Update existing game
- `GET /games` - List all games
- `GET /games/<id>` - Get specific game

See the main README for detailed API documentation.

