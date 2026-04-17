"""Application configuration and environment setup."""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GAMES_DIR = os.path.join(os.path.dirname(__file__), "games")

if not GEMINI_API_KEY or not CLAUDE_API_KEY:
    raise ValueError("GEMINI_API_KEY and CLAUDE_API_KEY must be set as environment variables")

if not os.path.exists(GAMES_DIR):
    os.makedirs(GAMES_DIR)
