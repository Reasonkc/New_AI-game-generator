"""Claude generation pipeline: streaming calls + two-pass (generate + self-review) + retry.

The Anthropic client is passed in rather than imported here — this keeps the module
testable (callers can inject a mock) and removes a hidden dependency on config.
"""
import logging
import time

from config import GENERATION_CONFIG
from prompts import GAME_SYSTEM_PROMPT_2D, GAME_SYSTEM_PROMPT_3D
from validation import extract_html_from_response, validate_game_html

logger = logging.getLogger(__name__)


def _stream_claude(client, messages: list, system: str,
                   temperature: float = None, max_tokens: int = None):
    """Stream a Claude completion. Returns (text, usage_dict)."""
    temp = GENERATION_CONFIG["temperature"] if temperature is None else temperature
    tokens = GENERATION_CONFIG["max_tokens"] if max_tokens is None else max_tokens
    buf: list[str] = []
    usage = {"input_tokens": 0, "output_tokens": 0}
    with client.messages.stream(
        model=GENERATION_CONFIG["model"],
        max_tokens=tokens,
        temperature=temp,
        system=system,
        messages=messages,
    ) as stream:
        for chunk in stream.text_stream:
            buf.append(chunk)
        try:
            final = stream.get_final_message()
            if final and getattr(final, "usage", None):
                usage = {
                    "input_tokens": int(getattr(final.usage, "input_tokens", 0) or 0),
                    "output_tokens": int(getattr(final.usage, "output_tokens", 0) or 0),
                }
        except Exception:
            pass
    return "".join(buf), usage


def _accum(a: dict, b: dict) -> None:
    a["input_tokens"] = a.get("input_tokens", 0) + b.get("input_tokens", 0)
    a["output_tokens"] = a.get("output_tokens", 0) + b.get("output_tokens", 0)


def generate_game_with_retry(client, user_prompt_text: str, engine_key: str, genre: str):
    """Two-pass generation (generate + self-review) with up to max_retries attempts.

    Returns (html, attempts_log, warnings_list, total_usage).
    """
    engine_tag = "3d" if engine_key == "threejs" else "2d"
    system_prompt = GAME_SYSTEM_PROMPT_3D if engine_tag == "3d" else GAME_SYSTEM_PROMPT_2D
    genre_line = f"Genre detected: {genre}. Apply relevant genre-specific rules."
    base_user = f"{genre_line}\n\n{user_prompt_text}"
    review_msg = (
        "Review this game against the 14 technical requirements in your system prompt. "
        "If any are violated, output the corrected full HTML file. "
        "If all pass, output the file unchanged. Output ONLY the HTML, no explanation."
    )

    attempts: list[dict] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    best_html = ""
    best_failures: list[str] = ["no attempts completed"]

    for attempt_num in range(1, GENERATION_CONFIG["max_retries"] + 1):
        attempt_start = time.time()
        attempt_usage = {"input_tokens": 0, "output_tokens": 0}
        attempt_failures: list[str] = []
        passed = False
        current_html = ""

        try:
            if attempt_num == 1:
                messages = [{"role": "user", "content": base_user}]
            else:
                fail_list = "\n".join(f"- {f}" for f in best_failures)
                retry_msg = (
                    f"Your previous output failed these checks:\n{fail_list}\n\n"
                    "Regenerate the complete HTML file fixing all issues. "
                    "Output only the HTML, no explanation."
                )
                messages = [
                    {"role": "user", "content": base_user},
                    {"role": "assistant", "content": best_html or "(empty previous output)"},
                    {"role": "user", "content": retry_msg},
                ]
            gen_text, gen_usage = _stream_claude(client, messages=messages, system=system_prompt)
            _accum(attempt_usage, gen_usage)
            gen_html = extract_html_from_response(gen_text)

            review_messages = [
                {"role": "user", "content": base_user},
                {"role": "assistant", "content": gen_html},
                {"role": "user", "content": review_msg},
            ]
            rev_text, rev_usage = _stream_claude(client, messages=review_messages, system=system_prompt)
            _accum(attempt_usage, rev_usage)
            current_html = extract_html_from_response(rev_text)

            passed, attempt_failures = validate_game_html(current_html, engine=engine_tag)
        except Exception as e:
            attempt_failures = [f"exception: {type(e).__name__}: {e}"]
            logger.error(f"Attempt {attempt_num} exception: {e}")

        _accum(total_usage, attempt_usage)
        attempts.append({
            "attempt": attempt_num,
            "passed": passed,
            "failures": attempt_failures,
            "latency_s": round(time.time() - attempt_start, 2),
            "usage": attempt_usage,
        })

        if passed:
            return current_html, attempts, [], total_usage

        if current_html and (not best_html or len(attempt_failures) < len(best_failures)):
            best_html = current_html
            best_failures = attempt_failures

    warnings = [f"all {GENERATION_CONFIG['max_retries']} attempts failed validation"] + best_failures
    return best_html, attempts, warnings, total_usage
