"""Pure validation and normalization helpers.

Side-effect free by design: these functions take input, return results, and do
not touch the filesystem, the network, or any Flask context. Trivially testable.
"""
import logging
import re

logger = logging.getLogger(__name__)


def sanitize_game_id(game_id: str) -> str:
    """Validate game_id to prevent path traversal attacks."""
    if not re.match(r'^[a-f0-9-]{36}$', game_id or ""):
        raise ValueError("Invalid game ID format")
    return game_id


def extract_html_from_response(text: str) -> str:
    """Extract HTML from an LLM response, stripping markdown code fences if present."""
    original_length = len(text)
    text = re.sub(r'^```html\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```$', '', text, flags=re.MULTILINE)
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    cleaned_text = text.strip()

    logger.info(f"Original response length: {original_length}")
    logger.info(f"Cleaned HTML length: {len(cleaned_text)}")
    if cleaned_text and not cleaned_text.lower().endswith('</html>'):
        logger.warning("HTML response appears to be truncated - missing closing </html> tag")
    if cleaned_text.endswith('...'):
        logger.warning("Response appears to be truncated (ends with ...)")

    return cleaned_text


def detect_genre(user_request: str) -> str:
    """Classify the user's request into a coarse genre bucket via keyword matching."""
    s = (user_request or "").lower()
    if re.search(r'\b(snake|worm)\b', s):
        return 'snake'
    if re.search(r'\b(jump|platform(er)?|mario)\b', s):
        return 'platformer'
    if re.search(r'\b(shoot(er)?|space\s*invaders?|invader|galaga|bullet\s*hell)\b', s):
        return 'shooter'
    if re.search(r'\b(match[- ]?3|tetris|sudoku|puzzle|2048)\b', s):
        return 'puzzle'
    return 'arcade'


def validate_game_html(html: str, engine: str = "2d") -> tuple[bool, list[str]]:
    """Static checks against the 14-rule contract.

    Engine-aware: 2D expects a <canvas>; 3D expects Three.js WebGLRenderer setup.
    Returns (passed, failures). passed is False iff failures is non-empty.
    """
    failures: list[str] = []
    if not html:
        return False, ["empty output"]

    low = html.lower()
    stripped = html.lstrip().lower()

    if not stripped.startswith('<!doctype html>'):
        failures.append("must start with <!DOCTYPE html>")

    if engine == "3d":
        if 'webglrenderer' not in low and 'renderer.domelement' not in low:
            failures.append("3D: missing THREE.WebGLRenderer setup")
        r128_forbidden = [
            "CapsuleGeometry",
            "RoundedBoxGeometry",
            "TextGeometry",
        ]
        for name in r128_forbidden:
            if re.search(rf'\bTHREE\.{name}\b', html):
                failures.append(f"3D: uses THREE.{name} which does not exist in r128")
    else:
        if '<canvas' not in low:
            failures.append("missing <canvas> element")

    if 'requestanimationframe' not in low:
        failures.append("missing requestAnimationFrame for main loop")

    if 'addeventlistener' not in low or 'keydown' not in low:
        failures.append("missing window.addEventListener('keydown', ...)")

    if 'preventdefault' not in low:
        failures.append("missing e.preventDefault() on game keys")

    if 'try' not in low or 'catch' not in low:
        failures.append("missing try/catch around main loop")

    if not re.search(r'\bCONFIG\b', html):
        failures.append("missing CONFIG object at top of script")

    if re.search(r'\bsetInterval\s*\(', html):
        failures.append("uses setInterval — replace with requestAnimationFrame-driven logic")

    if 'location.reload' in low:
        failures.append("uses location.reload — R must reset state in place")

    if re.search(r'''type\s*=\s*["']module["']''', html):
        failures.append('uses type="module" — must be a classic script')

    if len(html) < 2000:
        failures.append(f"file too short ({len(html)} chars) — likely truncated")

    script_open = len(re.findall(r'<script\b', html, flags=re.IGNORECASE))
    script_close = len(re.findall(r'</script\s*>', html, flags=re.IGNORECASE))
    if script_open != script_close:
        failures.append(f"unbalanced <script> tags ({script_open} open vs {script_close} close)")

    style_open = len(re.findall(r'<style\b', html, flags=re.IGNORECASE))
    style_close = len(re.findall(r'</style\s*>', html, flags=re.IGNORECASE))
    if style_open != style_close:
        failures.append(f"unbalanced <style> tags ({style_open} open vs {style_close} close)")

    return (len(failures) == 0, failures)
