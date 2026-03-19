# Backend Architecture

## Module Structure

```
backend/
├── backend.py          # Flask app entry point — route definitions only
├── config.py           # Environment variables, API keys, directory paths
├── utils.py            # Input validation (sanitize_game_id) and response processing
├── prompts.py          # AI prompt templates (Gemini enhance, Claude generate/update)
├── game_storage.py     # Game file I/O (save, load, list, update, serve)
├── gameCreator.py      # Legacy: Gemini-based multi-step game creation pipeline
├── gamemaker.py        # Legacy: Claude-based game generation (standalone)
├── screenshot.py       # Playwright-based game screenshot capture
├── tests/
│   ├── conftest.py     # Shared pytest fixtures (test client, mocked APIs)
│   └── test_utils.py   # Unit tests for utility functions
└── games/              # Runtime storage for generated game files
    └── <uuid>/
        ├── index.html
        └── metadata.json
```

## Dependency Graph

```
backend.py (routes)
├── config.py           ← env vars, paths
├── utils.py            ← sanitize_game_id(), extract_html_from_response()
├── prompts.py          ← build_enhance_prompt(), build_generate_prompt(), build_update_prompt()
├── game_storage.py     ← save_game(), load_game(), list_all_games(), update_game_file()
│   ├── config.py       ← GAMES_DIR
│   └── utils.py        ← sanitize_game_id()
├── flask / flask_cors / flask_limiter
├── google.genai        ← Gemini API (prompt enhancement)
└── anthropic           ← Claude API (game generation)
```

## Data Flow

```
User Prompt
    │
    ▼
[POST /enhance_prompt]
    │  → prompts.build_enhance_prompt()
    │  → Gemini API
    │  → Return enhanced concept
    ▼
[POST /generate_game]
    │  → prompts.build_generate_prompt()
    │  → Claude API
    │  → utils.extract_html_from_response()
    │  → game_storage.save_game()
    │  → Return game_id + play_url
    ▼
[GET /play_game/<id>]
    │  → game_storage.get_game_html_path()
    │  → Serve HTML with CSP headers
    ▼
[POST /update_game]
    │  → prompts.build_update_prompt()
    │  → Claude API
    │  → utils.extract_html_from_response()
    │  → game_storage.update_game_file()
    │  → Return updated HTML
```

## Design Decisions

1. **Thin routing layer**: `backend.py` contains only route handlers and Flask setup. No business logic, no file I/O, no prompt construction.

2. **Prompt templates isolated**: `prompts.py` holds all AI prompt strings. This makes it easy to tune prompts without touching route logic, and prevents merge conflicts when multiple developers work on different areas.

3. **Storage abstraction**: `game_storage.py` encapsulates all file system operations behind simple functions. If we migrate to cloud storage (S3, etc.), only this file changes.

4. **Config centralized**: `config.py` is the single source of truth for environment variables and paths. No module reads `os.getenv()` directly.
