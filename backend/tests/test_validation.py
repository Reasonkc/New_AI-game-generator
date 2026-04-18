"""Tests for validation.py — pure-function coverage with no Flask dependencies."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validation import detect_genre, validate_game_html


SEED_PATH = os.path.join(os.path.dirname(__file__), "..", "seed_example.html")


class TestDetectGenre:
    def test_snake(self):
        assert detect_genre("build me a snake game") == "snake"

    def test_worm_synonym(self):
        assert detect_genre("a worm eating dots") == "snake"

    def test_platformer(self):
        assert detect_genre("mario style platformer") == "platformer"

    def test_jump_keyword(self):
        assert detect_genre("a game where you jump over pits") == "platformer"

    def test_shooter(self):
        assert detect_genre("space invaders clone") == "shooter"

    def test_bullet_hell(self):
        assert detect_genre("bullet hell shmup") == "shooter"

    def test_puzzle_tetris(self):
        assert detect_genre("tetris variant") == "puzzle"

    def test_puzzle_2048(self):
        assert detect_genre("2048 style merging") == "puzzle"

    def test_default_arcade(self):
        assert detect_genre("something weird") == "arcade"

    def test_empty_input(self):
        assert detect_genre("") == "arcade"

    def test_none_input(self):
        assert detect_genre(None) == "arcade"


class TestValidateGameHtml2D:
    def test_seed_example_passes(self):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            seed = f.read()
        passed, failures = validate_game_html(seed, engine="2d")
        assert passed is True
        assert failures == []

    def test_empty_rejected(self):
        passed, failures = validate_game_html("", engine="2d")
        assert passed is False
        assert "empty output" in failures

    def test_missing_doctype(self):
        html = "<html><canvas></canvas><script>requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());try{}catch{}const CONFIG={};</script></html>" + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("<!DOCTYPE html>" in f for f in failures)

    def test_missing_canvas(self):
        html = "<!DOCTYPE html><html><script>requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());try{}catch{}const CONFIG={};</script></html>" + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("canvas" in f.lower() for f in failures)

    def test_missing_raf(self):
        html = "<!DOCTYPE html><html><canvas></canvas><script>window.addEventListener('keydown',e=>e.preventDefault());try{}catch{}const CONFIG={};</script></html>" + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("requestAnimationFrame" in f for f in failures)

    def test_uses_setInterval_rejected(self):
        html = ("<!DOCTYPE html><html><canvas></canvas><script>"
                "requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());"
                "try{}catch{}const CONFIG={};setInterval(fn,16);</script></html>") + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("setInterval" in f for f in failures)

    def test_uses_location_reload_rejected(self):
        html = ("<!DOCTYPE html><html><canvas></canvas><script>"
                "requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());"
                "try{}catch{}const CONFIG={};location.reload();</script></html>") + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("location.reload" in f for f in failures)

    def test_uses_type_module_rejected(self):
        html = ('<!DOCTYPE html><html><canvas></canvas><script type="module">'
                "requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());"
                "try{}catch{}const CONFIG={};</script></html>") + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any('type="module"' in f for f in failures)

    def test_unbalanced_script_tags(self):
        html = ("<!DOCTYPE html><html><canvas></canvas>"
                "<script>requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());"
                "try{}catch{}const CONFIG={};"
                "<script>unclosed</html>") + "x" * 2100
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("unbalanced <script>" in f for f in failures)

    def test_too_short(self):
        html = "<!DOCTYPE html><html><canvas></canvas><script>requestAnimationFrame; window.addEventListener('keydown',e=>e.preventDefault()); try{}catch{}; const CONFIG={};</script></html>"
        passed, failures = validate_game_html(html, engine="2d")
        assert passed is False
        assert any("too short" in f for f in failures)


class TestValidateGameHtml3D:
    def _valid_3d_skeleton(self) -> str:
        body = ("<!DOCTYPE html><html><body>"
                "<script src='three.min.js'></script>"
                "<script>"
                "const renderer = new THREE.WebGLRenderer();"
                "document.body.appendChild(renderer.domElement);"
                "window.addEventListener('keydown', e => e.preventDefault());"
                "requestAnimationFrame(frame);"
                "try { } catch (e) { }"
                "const CONFIG = { dt: 1/60 };"
                "</script></body></html>")
        return body + "x" * 2100

    def test_valid_3d_passes(self):
        passed, failures = validate_game_html(self._valid_3d_skeleton(), engine="3d")
        assert passed is True
        assert failures == []

    def test_3d_missing_webgl_renderer(self):
        html = ("<!DOCTYPE html><html><body><script>"
                "requestAnimationFrame;window.addEventListener('keydown',e=>e.preventDefault());"
                "try{}catch{}const CONFIG={};"
                "</script></body></html>") + "x" * 2100
        passed, failures = validate_game_html(html, engine="3d")
        assert passed is False
        assert any("WebGLRenderer" in f for f in failures)

    def test_3d_rejects_r128_forbidden_geometry(self):
        bad = self._valid_3d_skeleton().replace("three.min.js'></script>",
            "three.min.js'></script><script>new THREE.CapsuleGeometry(1,2,3);</script>")
        passed, failures = validate_game_html(bad, engine="3d")
        assert passed is False
        assert any("CapsuleGeometry" in f for f in failures)
