"""Flask middleware for performance monitoring."""

import time
import logging

logger = logging.getLogger(__name__)

# In-memory stats tracker
_stats = {
    "total_requests": 0,
    "total_games_generated": 0,
    "generation_failures": 0,
    "response_times": [],
}


def get_stats():
    """Return current application stats."""
    times = _stats["response_times"]
    avg_time = sum(times) / len(times) if times else 0
    return {
        "total_requests": _stats["total_requests"],
        "total_games_generated": _stats["total_games_generated"],
        "generation_failures": _stats["generation_failures"],
        "avg_response_time_ms": round(avg_time, 2),
    }


def track_generation(success=True):
    """Track a game generation attempt."""
    if success:
        _stats["total_games_generated"] += 1
    else:
        _stats["generation_failures"] += 1


def init_middleware(app):
    """Attach request timing middleware to Flask app."""

    @app.before_request
    def start_timer():
        from flask import g
        g.start_time = time.time()

    @app.after_request
    def log_response_time(response):
        from flask import g, request
        if hasattr(g, "start_time"):
            elapsed_ms = (time.time() - g.start_time) * 1000
            _stats["total_requests"] += 1
            _stats["response_times"].append(elapsed_ms)
            # Keep only last 1000 entries
            if len(_stats["response_times"]) > 1000:
                _stats["response_times"] = _stats["response_times"][-1000:]
            logger.info(f"{request.method} {request.path} — {elapsed_ms:.1f}ms — {response.status_code}")
        return response
