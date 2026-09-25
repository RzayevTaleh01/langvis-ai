"""
web/bridge.py - how the live session reaches the page.

core/live.LiveSession talks to its interface through a few calls (set_state,
write_log, set_live_sentence, send, ...). WebUI turns each one into a message
for every open browser tab.
"""
from __future__ import annotations

import asyncio
import json
import threading
from collections import deque
from typing import Callable

from memory.config_manager import is_configured


class WebUI:
    """The interface the live session and the tutor plugin talk to, as
    messages to the browser.

    Called from the event loop, from the tutor's worker thread and from tool
    threads alike, so every send is handed to the loop thread-safely.
    """

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: set = set()
        self._clients_lock = threading.Lock()
        self.key_ready = is_configured()
        self.muted = False
        self.hold_live = False
        self.state = "SLEEPING"
        self.live_sentence = {"text": "", "final": True}
        self.log: deque[str] = deque(maxlen=300)

        # Set by the server: every conversation line, to be kept.
        self.on_line: Callable | None = None
        # Set by LiveSession: the tutor plugin speaks through these.
        self.request_say: Callable | None = None
        self.request_say_when_idle: Callable | None = None
        self.request_context: Callable | None = None

    # ── Plumbing ─────────────────────────────────────────────────────────────

    def attach(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def add_client(self, ws) -> None:
        with self._clients_lock:
            self._clients.add(ws)

    def remove_client(self, ws) -> None:
        with self._clients_lock:
            self._clients.discard(ws)

    async def close_all(self, message: dict) -> None:
        """Every open tab is told why, and disconnected: another account is
        signed in on this computer, or this one signed out."""
        with self._clients_lock:
            clients = list(self._clients)
            self._clients.clear()
        for ws in clients:
            try:
                await ws.send_str(json.dumps(message, ensure_ascii=False))
                await ws.close()
            except Exception:
                pass

    def has_clients(self) -> bool:
        with self._clients_lock:
            return bool(self._clients)

    def snapshot(self) -> list[dict]:
        """What a tab that has just opened needs to catch up."""
        return [
            {"type": "state", "state": self.state},
            {"type": "muted", "value": self.muted},
            {"type": "live_sentence", **self.live_sentence},
            {"type": "log_history", "lines": list(self.log)},
            {"type": "need_key", "value": not self.key_ready},
        ]

    def _send(self, message: dict | bytes) -> None:
        loop = self._loop
        if loop is None:
            return
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            loop.create_task(self._broadcast(message))
        else:
            asyncio.run_coroutine_threadsafe(self._broadcast(message), loop)

    async def _broadcast(self, message: dict | bytes) -> None:
        with self._clients_lock:
            clients = list(self._clients)
        for ws in clients:
            try:
                if isinstance(message, (bytes, bytearray)):
                    await ws.send_bytes(bytes(message))
                else:
                    await ws.send_str(json.dumps(message, ensure_ascii=False))
            except Exception:
                self.remove_client(ws)

    def send(self, message: dict) -> None:
        self._send(message)

    def send_audio(self, pcm: bytes) -> None:
        self._send(pcm)

    # ── The calls the session and the plugin make ────────────────────────────

    def set_state(self, state: str) -> None:
        # The player reports "speaking" for every chunk it releases; the page
        # only needs to hear about a change.
        if state == self.state:
            return
        self.state = state
        self._send({"type": "state", "state": state})

    def write_log(self, text: str) -> None:
        text = str(text)
        self.log.append(text)
        # The learner's and the tutor's lines are the conversation: kept.
        who, _, body = text.partition(": ")
        if body and who not in ("SYS", "ERR", "NET") and self.on_line:
            try:
                self.on_line(who, body)
            except Exception as e:
                print(f"[Web] history: {e}")
        self._send({"type": "log", "text": text})

    def set_live_sentence(self, text: str, final: bool = False) -> None:
        # While a thought-through turn is answered, the board already shows the
        # sentence as the analyser heard it; the live transcript that arrives
        # late must not overwrite it.
        if self.hold_live:
            return
        self.live_sentence = {"text": text, "final": bool(final)}
        self._send({"type": "live_sentence", "text": text, "final": bool(final)})

    def reset(self) -> None:
        """A fresh lesson: every open tab clears its board and transcript."""
        self.log.clear()
        self.hold_live = False
        self.live_sentence = {"text": "", "final": True}
        self._send({"type": "reset"})

    def show_content(self, title: str, text: str) -> None:
        self._send({"type": "content", "title": str(title), "text": str(text)})

    def prompt_reconfig(self) -> None:
        self.key_ready = False
        self._send({"type": "need_key", "value": True})

    def key_saved(self) -> None:
        self.key_ready = True
        self._send({"type": "need_key", "value": False})
