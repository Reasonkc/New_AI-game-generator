"""Centralized configuration: env vars, paths, model settings, and API clients.

Everything that would require changing if a deployment target or credential changes
lives here. No route logic, no business logic — just wiring.
"""
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
if not GEMINI_API_KEY or not CLAUDE_API_KEY:
    raise ValueError("API keys must be set as environment variables")

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
GAMES_DIR = os.path.join(BACKEND_DIR, "games")
LOGS_DIR = os.path.join(BACKEND_DIR, "logs")
os.makedirs(GAMES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

GENERATIONS_LOG = os.path.join(LOGS_DIR, "generations.jsonl")
BUG_REPORTS_LOG = os.path.join(LOGS_DIR, "bug_reports.jsonl")

GENERATION_CONFIG = {
    "model": os.getenv("GAME_MODEL", "claude-sonnet-4-20250514"),
    "temperature": float(os.getenv("GAME_TEMPERATURE", "0.3")),
    "max_tokens": int(os.getenv("GAME_MAX_TOKENS", "12000")),
    "max_retries": int(os.getenv("GAME_MAX_RETRIES", "1")),
    "strict_validation": os.getenv("GAME_STRICT_VALIDATION", "1") == "1",
}

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
