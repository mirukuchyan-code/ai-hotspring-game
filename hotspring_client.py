"""Tiny public client for AI players.

This file is safe to publish. It only talks to a referee server and does not
contain hidden event logic or achievement trigger conditions.
"""

from __future__ import annotations

import json
import sys
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class HotSpringClient:
    def __init__(self, base_url: str = "https://taoyuan-hotspring.onrender.com", session_id: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        req = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(text) from exc

    def new_game(self) -> dict[str, Any]:
        data = self._request("POST", "/new", {})
        self.session_id = data["session_id"]
        return data

    def state(self) -> dict[str, Any]:
        if not self.session_id:
            raise ValueError("No session_id. Call new_game() first or pass a session_id.")
        query = urlencode({"session_id": self.session_id})
        return self._request("GET", f"/state?{query}")

    def act(self, action: str = "wait", **kwargs: Any) -> dict[str, Any]:
        if not self.session_id:
            raise ValueError("No session_id. Call new_game() first or pass a session_id.")
        payload = {"session_id": self.session_id, "action": action, **kwargs}
        return self._request("POST", "/act", payload)


if __name__ == "__main__":
    client = HotSpringClient()
    start = client.new_game()
    print("session_id:", client.session_id)
    print(json.dumps(start["state"], ensure_ascii=False, indent=2))
    print(json.dumps(client.act("wait"), ensure_ascii=False, indent=2))
