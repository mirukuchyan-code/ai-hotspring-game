"""Private referee server for Taoyuan Hot Spring Village.

Do NOT publish this folder if you want to keep event logic and achievement
conditions hidden. Publish only the files in public_github_repo.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import hotspring_engine

ROOT = Path(__file__).resolve().parent
VERSION = "0.2.1"
SAVE_DIR = Path(os.environ.get("SAVE_DIR", ROOT / "saves"))
SAVE_DIR.mkdir(parents=True, exist_ok=True)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8765"))
_lock = threading.RLock()
_sessions: dict[str, hotspring_engine.HotSpringGame] = {}


def _save_path(session_id: str) -> Path:
    safe = "".join(ch for ch in session_id if ch.isalnum() or ch in "_-")
    if not safe:
        raise ValueError("invalid session_id")
    return SAVE_DIR / f"{safe}.json"


def _with_save_file(path: Path):
    hotspring_engine.SAVE_FILE = str(path)


def _state_for(game: hotspring_engine.HotSpringGame) -> dict:
    state = game.get_state()
    # Keep API state public: names of unlocked achievements are OK, but no hidden
    # trigger conditions or event tables are exposed here.
    return state


def _new_game() -> tuple[str, dict]:
    session_id = secrets.token_urlsafe(10)
    path = _save_path(session_id)
    with _lock:
        _with_save_file(path)
        game = hotspring_engine.HotSpringGame(load_from_file=False)
        game._save_game()
        _sessions[session_id] = game
        return session_id, _state_for(game)


def _load_game(session_id: str) -> hotspring_engine.HotSpringGame:
    with _lock:
        if session_id in _sessions:
            return _sessions[session_id]
        path = _save_path(session_id)
        if not path.exists():
            raise KeyError("unknown session_id")
        _with_save_file(path)
        game = hotspring_engine.HotSpringGame(load_from_file=True)
        _sessions[session_id] = game
        return game


def _save_game(session_id: str, game: hotspring_engine.HotSpringGame) -> None:
    with _lock:
        _with_save_file(_save_path(session_id))
        before = len(game._log)
        game._save_game()
        if len(game._log) > before and game._log[-1] == "💾 游戏已保存！":
            game._log.pop()


class Handler(BaseHTTPRequestHandler):
    server_version = "TaoyuanHotSpring/0.1"

    def log_message(self, fmt: str, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("content-length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        try:
            if parsed.path == "/health":
                self._json(200, {"ok": True, "game": "桃源温泉乡", "version": VERSION})
                return
            if parsed.path == "/state":
                session_id = query.get("session_id", [""])[0]
                game = _load_game(session_id)
                self._json(200, {"ok": True, "session_id": session_id, "state": _state_for(game)})
                return
            self._json(404, {"ok": False, "error": "not found"})
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self._body()
            if parsed.path == "/new":
                session_id, state = _new_game()
                self._json(200, {"ok": True, "session_id": session_id, "state": state})
                return
            if parsed.path == "/act":
                session_id = payload.pop("session_id", "")
                action = payload.get("action")
                if isinstance(action, dict):
                    action_payload = action
                else:
                    action_payload = payload
                # One session action is a single transaction. This prevents two
                # concurrent AI players from advancing the same save at once.
                with _lock:
                    game = _load_game(session_id)
                    result = game.act(action_payload)
                    _save_game(session_id, game)
                self._json(200, {"ok": True, "session_id": session_id, "result": result})
                return
            self._json(404, {"ok": False, "error": "not found"})
        except Exception as exc:
            self._json(400, {"ok": False, "error": str(exc)})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"桃源温泉乡私有裁判服务器：http://{HOST}:{PORT}")
    print("公开 GitHub 仓库只需要放 public_github_repo，不要放 private_server。")
    server.serve_forever()


if __name__ == "__main__":
    main()
