"""
web/server.py - LangVis in the browser.

One local aiohttp server: the page and its files, one WebSocket per tab, a few
JSON endpoints for the pages, and the live Gemini session (core/live.py) on the
same event loop.

Socket protocol
    browser → server   binary: 16 kHz mono int16 microphone blocks
                       text:   {"type": "start" | "restart" | "text" | "interrupt" | "mute" |
                                "topic" | "undo" | "explain" | "fluency" | "skip", ...}
    server → browser   binary: 24 kHz mono int16 tutor voice
                       text:   {"type": "state" | "mode" | "log" | "live_sentence" | "hearing" |
                                "repeat" | "lesson" | "frames" | "tutor_words" | "status" |
                                "coaching" | "syllabus" |
                                "reset" | "flush" | "need_key" | "notice" | ...}

The session is started by the first "start" from a tab, not at launch: the
browser may only play sound after a click, and a lesson that greets an empty
room wastes the opening and the API quota.
"""
from __future__ import annotations

import asyncio
import json
import webbrowser
from pathlib import Path

from aiohttp import WSMsgType, web

from core.live import LiveSession, plugin_fn
from memory.memory_manager import all_entries_for_ui, forget
from memory.config_manager import (
    AVAILABLE_VOICES, get_assistant_name, get_gemini_keys, get_plugin_config, get_user_name,
    get_voice, is_configured, save_api_keys, save_assistant_config, save_plugin_config,
    save_voice, set_gemini_keys,
)
from web.bridge import WebUI

STATIC_DIR = Path(__file__).resolve().parent / "static"
HOST = "127.0.0.1"
PORT = 8765
PUSH_INTERVAL = 0.5     # seconds between checks for changed status / card / syllabus


class App:
    def __init__(self) -> None:
        self.ui = WebUI()
        self.live: LiveSession | None = None
        self._session_task: asyncio.Task | None = None
        self._pushed: dict[str, str] = {}

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def on_startup(self, _app: web.Application) -> None:
        loop = asyncio.get_running_loop()
        self.ui.attach(loop)
        self.live = LiveSession(self.ui)

        def keep(who: str, text: str) -> None:
            fn = plugin_fn("record_line")
            if fn is not None:
                loop.run_in_executor(None, fn, who, text)
        self.ui.on_line = keep
        asyncio.get_running_loop().create_task(self._push_loop())

    def _start_session(self) -> None:
        if self._session_task and not self._session_task.done():
            return
        if not is_configured():
            self.ui.prompt_reconfig()
            return
        self._session_task = asyncio.get_running_loop().create_task(self.live.run())

    # ── Status, board and syllabus: pushed when they change ──────────────────

    async def _push_loop(self) -> None:
        while True:
            await asyncio.sleep(PUSH_INTERVAL)
            if not self.ui.has_clients() or self.live is None:
                continue
            for kind, getter in (("status", self.live.lesson_status),
                                 ("coaching", self.live.coaching),
                                 ("syllabus", self.live.syllabus)):
                try:
                    value = await asyncio.to_thread(getter)
                except Exception as e:
                    print(f"[Web] {kind}: {e}")
                    continue
                blob = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
                if self._pushed.get(kind) != blob:
                    self._pushed[kind] = blob
                    self.ui.send({"type": kind, "data": value})

    # ── HTTP ─────────────────────────────────────────────────────────────────

    async def index(self, _request: web.Request) -> web.FileResponse:
        return web.FileResponse(STATIC_DIR / "index.html",
                                headers={"Cache-Control": "no-store"})

    async def save_key(self, request: web.Request) -> web.Response:
        if not _same_origin(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        body = await _json_body(request)
        key = str(body.get("key") or "").strip()
        if len(key) < 16:
            return web.json_response({"ok": False, "error": "That does not look like a key."},
                                     status=400)
        await asyncio.to_thread(save_api_keys, key)
        self.ui.key_saved()
        return web.json_response({"ok": True})

    # ── Gemini keys, from Settings ───────────────────────────────────────────

    async def get_keys(self, _request: web.Request) -> web.Response:
        """The keys, masked - the page never gets a whole key back."""
        keys = await asyncio.to_thread(get_gemini_keys)
        return _json({"keys": [{"id": _key_id(k), "masked": _mask(k), "main": i == 0}
                               for i, k in enumerate(keys)]})

    async def post_keys(self, request: web.Request) -> web.Response:
        """{action: add, key, main} | {action: remove, id} | {action: main, id}"""
        if not _same_origin(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        body = await _json_body(request)
        action = str(body.get("action") or "")
        keys = await asyncio.to_thread(get_gemini_keys)
        main_before = keys[0] if keys else ""
        if action == "add":
            key = str(body.get("key") or "").strip()
            if len(key) < 16:
                return web.json_response({"ok": False, "error": "That does not look like a key."})
            problem = await asyncio.to_thread(_check_key, key)
            if problem:
                return web.json_response({"ok": False, "error": problem})
            keys = [k for k in keys if k != key]
            keys = [key] + keys if body.get("main") or not keys else keys + [key]
        elif action in ("remove", "main"):
            found = next((k for k in keys if _key_id(k) == body.get("id")), None)
            if not found:
                return web.json_response({"ok": False, "error": "That key is not saved."})
            if action == "remove":
                if len(keys) == 1:
                    return web.json_response({"ok": False, "error": "The last key cannot be removed."})
                keys = [k for k in keys if k != found]
            else:
                keys = [found] + [k for k in keys if k != found]
        else:
            return web.json_response({"ok": False, "error": "unknown action"}, status=400)
        await asyncio.to_thread(set_gemini_keys, keys[0], keys[1:])
        self.ui.key_saved()
        if keys[0] != main_before and self.live:
            # The voice session was opened with the old main key.
            self.live.request_reconnect(keep_context=True, reason="a new Gemini key")
        return web.json_response({"ok": True})

    async def data(self, request: web.Request) -> web.Response:
        """The account and dictionary pages ask for their data when opened."""
        getter = {"account": "account_for_ui",
                  "dictionary": "dictionary_for_ui"}.get(request.match_info["page"])
        fn = plugin_fn(getter) if getter else None
        if fn is None:
            return web.json_response({"error": "not available"}, status=404)
        try:
            value = await asyncio.to_thread(fn)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
        return _json(value)

    async def get_settings(self, _request: web.Request) -> web.Response:
        """The settings form: the tutor plugin's own fields, plus names and voice."""
        schemas = self.live._plugin_registry.settings_schemas() if self.live else []
        for schema in schemas:
            schema["values"] = get_plugin_config(schema["namespace"])
        return _json({"plugins": schemas, "voice": get_voice(), "voices": AVAILABLE_VOICES,
                      "assistant_name": get_assistant_name(), "user_name": get_user_name()})

    async def put_settings(self, request: web.Request) -> web.Response:
        if not _same_origin(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        body = await _json_body(request)
        old_voice, old_names = get_voice(), (get_assistant_name(), get_user_name())
        for namespace, values in (body.get("plugins") or {}).items():
            if isinstance(values, dict):
                before = get_plugin_config(namespace)
                await asyncio.to_thread(save_plugin_config, namespace, values)
                await asyncio.to_thread(self._apply_tutor_settings, before, values)
        if body.get("voice"):
            await asyncio.to_thread(save_voice, str(body["voice"]))
        names = (str(body.get("assistant_name") or old_names[0]),
                 str(body.get("user_name") if body.get("user_name") is not None else old_names[1]))
        if names != old_names:
            await asyncio.to_thread(save_assistant_config, *names)
        if self.live:
            # Voice, names, pace and strictness live in the session's system
            # prompt; a new voice also needs a fresh start (resuming would keep
            # the old one).
            fresh = get_voice() != old_voice
            self.live.request_reconnect(keep_context=not fresh, reason="new settings")
        return web.json_response({"ok": True})

    async def get_history(self, request: web.Request) -> web.Response:
        """The whole conversation of a topic, for the transcript."""
        fn = plugin_fn("history_for_ui")
        if fn is None:
            return _json({"topic": "", "lines": []})
        return _json(await asyncio.to_thread(fn, request.query.get("topic", "")))

    async def get_memory(self, _request: web.Request) -> web.Response:
        """What LangVis remembers about the learner, for the settings page."""
        return _json(await asyncio.to_thread(all_entries_for_ui))

    async def forget_memory(self, request: web.Request) -> web.Response:
        if not _same_origin(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        body = await _json_body(request)
        message = await asyncio.to_thread(forget, str(body.get("key") or ""),
                                          str(body.get("category") or "notes"))
        return web.json_response({"ok": message.startswith("Forgotten"), "message": message})

    @staticmethod
    def _apply_tutor_settings(before: dict, values: dict) -> None:
        """Settings that are also facts in the learner's progress file."""
        run = plugin_fn("run")
        if run is None:
            return
        for key, action in (("starting_level", "set_level"), ("goal_level", "set_goal"),
                            ("mode", "set_mode")):
            if values.get(key) and values.get(key) != before.get(key):
                field = "mode" if key == "mode" else "level"
                run({"action": action, field: values[key]})

    # ── WebSocket ────────────────────────────────────────────────────────────

    async def socket(self, request: web.Request) -> web.WebSocketResponse:
        if not _same_origin(request):
            raise web.HTTPForbidden(text="origin")
        ws = web.WebSocketResponse(heartbeat=20, max_msg_size=1 << 20)
        await ws.prepare(request)
        for message in self.ui.snapshot():
            await ws.send_str(json.dumps(message, ensure_ascii=False))
        for kind in ("status", "coaching", "syllabus"):
            if kind in self._pushed:
                await ws.send_str(f'{{"type": "{kind}", "data": {self._pushed[kind]}}}')
        self.ui.add_client(ws)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.BINARY:
                    if self.live:
                        self.live.feed_mic(msg.data)
                elif msg.type == WSMsgType.TEXT:
                    try:
                        self._on_message(json.loads(msg.data))
                    except Exception as e:
                        print(f"[Web] bad message: {e}")
        finally:
            self.ui.remove_client(ws)
        return ws

    def _on_message(self, data: dict) -> None:
        kind = data.get("type")
        ui, live = self.ui, self.live
        if kind in ("start", "restart"):
            # A page that has just been opened (or reloaded) starts the lesson
            # again from nothing; a tab that only lost its connection does not.
            running = self._session_task is not None and not self._session_task.done()
            if running and (kind == "restart" or data.get("fresh")) and live:
                live.restart()
            else:
                self._start_session()
        elif kind == "text":
            text = str(data.get("text") or "").strip()
            if text and live and live.session:
                ui.write_log(f"You: {text}")
                # Checked before the tutor answers, exactly like a spoken sentence.
                asyncio.get_running_loop().create_task(live.typed(text))
        elif kind == "interrupt":
            if live:
                live.interrupt()
        elif kind == "mute":
            ui.muted = bool(data.get("value"))
            ui.send({"type": "muted", "value": ui.muted})
            ui.write_log("SYS: Microphone muted." if ui.muted else "SYS: Microphone on.")
            if not ui.muted and ui.state not in ("SPEAKING", "SLEEPING"):
                ui.set_state("LISTENING")
        elif kind == "topic":
            prompt = data.get("prompt")
            self._plugin_async("set_topic", str(data.get("id") or ""),
                               str(data.get("custom") or ""), ui,
                               None if prompt is None else str(prompt), False,
                               report=True, then=self._fresh_topic)
        elif kind == "undo":
            self._plugin_async("undo_last", ui, report=True)
        elif kind == "explain":
            item = data.get("item") if isinstance(data.get("item"), dict) else {}
            self._plugin_async("explain_request", item, ui)
        elif kind == "fluency":
            self._plugin_async("fluency_request", ui)
        elif kind == "delete_topic":
            self._plugin_async("delete_topic", str(data.get("id") or ""), ui, False,
                               report=True, then=self._fresh_topic)
        elif kind == "skip":
            self._plugin_async("skip_step", ui, report=True)

    def _fresh_topic(self, ok: bool, message: str) -> None:
        """A new topic (or a new scenario for this one, or the current topic
        deleted): a clean board and a new conversation in it, straight away."""
        if not ok or message.startswith("Already") or not self.live:
            return
        if message.startswith("Deleted") and "Back to free talk" not in message:
            return                          # another topic was deleted: nothing changes here
        running = self._session_task is not None and not self._session_task.done()
        if running:
            self.live.restart(new_topic=True)

    def _plugin_async(self, name: str, *args, report: bool = False, then=None) -> None:
        """Run a tutor-plugin call off the loop (they read and write files). A
        call that returns (ok, message) is reported back to the page, and
        handed to `then` on the loop."""
        fn = plugin_fn(name)
        if fn is None:
            self.ui.write_log(f"ERR: the tutor cannot do '{name}' right now.")
            return

        def work():
            try:
                result = fn(*args)
            except Exception as e:
                self.ui.write_log(f"ERR: {name} failed - {e}")
                return
            if report and isinstance(result, tuple) and len(result) == 2:
                ok, message = result
                self.ui.write_log(("SYS: " if ok else "ERR: ") + str(message))
                self.ui.send({"type": "notice", "ok": bool(ok), "text": str(message)})
                if then is not None:
                    loop.call_soon_threadsafe(then, bool(ok), str(message))

        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, work)


async def _json_body(request: web.Request) -> dict:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


def _key_id(key: str) -> str:
    import hashlib
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _mask(key: str) -> str:
    return f"{key[:4]}…{key[-4:]}"


def _check_key(key: str) -> str:
    """'' if Google accepts the key, otherwise why not. Listing models costs
    no quota."""
    try:
        from google import genai
        client = genai.Client(api_key=key)      # kept alive while the list is read
        next(iter(client.models.list()), None)
        return ""
    except Exception as e:
        err = str(e)
        if "API key not valid" in err or "API_KEY_INVALID" in err or "400" in err:
            return "Google does not accept this key."
        return f"The key could not be checked: {err[:80]}"


def _json(value) -> web.Response:
    return web.json_response(value, dumps=lambda v: json.dumps(v, ensure_ascii=False, default=str))


def _same_origin(request: web.Request) -> bool:
    """Only this page may drive the tutor. Any other site open in the same
    browser could otherwise connect to localhost and listen in."""
    origin = request.headers.get("Origin")
    if origin is None:
        return True        # not a browser page (curl, tests)
    return origin in (f"http://{request.host}", f"https://{request.host}")


@web.middleware
async def _no_stale_files(request: web.Request, handler):
    """The page is a handful of small local files: always revalidate them, so
    an update is never half-applied from the browser cache."""
    response = await handler(request)
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


def build_app() -> web.Application:
    state = App()
    app = web.Application(middlewares=[_no_stale_files])
    app.on_startup.append(state.on_startup)
    app.router.add_get("/", state.index)
    app.router.add_get("/ws", state.socket)
    app.router.add_post("/api/key", state.save_key)
    app.router.add_get("/api/settings", state.get_settings)
    app.router.add_post("/api/settings", state.put_settings)
    app.router.add_get("/api/memory", state.get_memory)
    app.router.add_get("/api/keys", state.get_keys)
    app.router.add_post("/api/keys", state.post_keys)
    app.router.add_get("/api/history", state.get_history)
    app.router.add_post("/api/memory/forget", state.forget_memory)
    app.router.add_get("/api/{page}", state.data)
    app.router.add_static("/static/", STATIC_DIR)
    app["state"] = state
    return app


def main(open_browser: bool = True) -> None:
    url = f"http://localhost:{PORT}/"
    print(f"⚙  LangVis - {url}")
    if open_browser:
        webbrowser.open(url)
    web.run_app(build_app(), host=HOST, port=PORT, print=None)
