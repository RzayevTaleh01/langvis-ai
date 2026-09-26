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

Accounts (web/auth.py): every endpoint but sign-in and the course catalog
needs a signed-in account. There is one microphone and one voice session, so
one account is in use at a time: when another account signs in, the lesson
stops, the open tabs of the last account are told ("seat_taken") and closed,
and core/profile.py points every read and write at the new account's rows.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import webbrowser
from pathlib import Path

from aiohttp import WSMsgType, web

from core import profile, store
from core.live import LiveSession, plugin_fn
from memory.memory_manager import all_entries_for_ui, forget
from memory.config_manager import (
    AVAILABLE_VOICES, adopt_legacy_settings, get_assistant_name, get_gemini_keys, get_plugin_config, get_user_name,
    get_voice, is_configured, save_api_keys, save_assistant_config, save_plugin_config,
    save_voice, set_gemini_keys, USER_KEYS,
)
from web.auth import Accounts, database_url
from web.bridge import WebUI

STATIC_DIR = Path(__file__).resolve().parent / "static"
# The Next.js page, built as static files (cd frontend && npm run build). When
# it is there it is the page; the old one in web/static is only a fallback.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "out"
# `next dev` runs the page on its own port while it is being worked on.
DEV_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")
HOST = "127.0.0.1"
PORT = 8765
PUSH_INTERVAL = 0.5     # seconds between checks for changed status / card / syllabus


class App:
    def __init__(self) -> None:
        self.ui = WebUI()
        self.live: LiveSession | None = None
        self._session_task: asyncio.Task | None = None
        self._pushed: dict[str, str] = {}
        self.accounts = Accounts(self.signed_in, self.signed_out)
        self.user_id: int | None = None      # the account in use
        self._seat = asyncio.Lock()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def on_startup(self, _app: web.Application) -> None:
        # Everything LangVis keeps lives in the database, next to the accounts.
        await asyncio.to_thread(store.open, database_url())
        await self._import_old_files()
        self.ui.key_ready = await asyncio.to_thread(is_configured)
        loop = asyncio.get_running_loop()
        self.ui.attach(loop)
        self.live = LiveSession(self.ui)

        def keep(who: str, text: str) -> None:
            fn = plugin_fn("record_line")
            if fn is not None:
                loop.run_in_executor(None, fn, who, text)
        self.ui.on_line = keep
        asyncio.get_running_loop().create_task(self._push_loop())

    async def _import_old_files(self) -> None:
        """Earlier versions kept everything in JSON files. They are moved into
        the database once, and deleted."""
        config = profile.BASE / "config" / "api_keys.json"
        if config.is_file() and await asyncio.to_thread(store.import_shared_config, config, USER_KEYS):
            print("[Web] The Gemini keys moved into the database.")
        ids = [r["id"] for r in await self.accounts.pool.fetch("SELECT id FROM users ORDER BY id")]
        if profile.USERS_DIR.is_dir():
            for folder in sorted(profile.USERS_DIR.glob("u*")):
                uid = int(folder.name[1:]) if folder.name[1:].isdigit() else None
                if uid in ids:
                    moved = await asyncio.to_thread(store.import_account_files, uid, folder,
                                                    profile.LEGACY_DIRS)
                    if moved:
                        print(f"[Web] Account {uid}: {len(moved)} file(s) moved into the database.")
                    if folder.is_dir() and not any(folder.rglob("*.*")):
                        await asyncio.to_thread(shutil.rmtree, folder, True)
            if not any(profile.USERS_DIR.iterdir()):
                profile.USERS_DIR.rmdir()
        if ids:
            await self._adopt_old_progress(ids[0])

    @staticmethod
    async def _adopt_old_progress(user_id: int) -> None:
        """The progress made before accounts existed belongs to the first account."""
        moved = await asyncio.to_thread(store.import_account_files, user_id, profile.BASE,
                                        profile.LEGACY_DIRS)
        await asyncio.to_thread(adopt_legacy_settings, user_id)
        if moved:
            print(f"[Web] The first account took over the earlier progress: {', '.join(moved)}")

    # ── Accounts: whose lesson this is ───────────────────────────────────────

    async def claim(self, user) -> None:
        """`user` is using LangVis now. If another account was, its lesson
        stops and its tabs are closed, and the files switch to this account."""
        uid = user["id"]
        if self.user_id == uid:
            return
        async with self._seat:
            if self.user_id == uid:
                return
            await self._leave({"type": "seat_taken", "by": user["name"]})
            await asyncio.to_thread(self._switch_files, uid)
            self.user_id = uid
            print(f"[Web] Account in use: {user['email']}")

    async def _leave(self, message: dict) -> None:
        """The account in use steps away: no lesson, no tab, nothing pushed."""
        self._stop_session()
        if self.live:
            self.live._session_log = []      # its lesson summary is not written for another
        await self.ui.close_all(message)
        self._pushed.clear()

    def _switch_files(self, user_id: int | None) -> None:
        profile.set_user(user_id)
        store.forget_user_cache()
        fn = plugin_fn("switch_user")
        if fn is not None:
            fn()
        self.ui.reset()

    async def signed_in(self, user, created: bool, first: bool) -> None:
        if created and first:
            # The first account takes over what was learned before accounts.
            await self._adopt_old_progress(user["id"])
        await self.claim(user)
        if created:
            await asyncio.to_thread(self._set_up_account, user)
            self._pushed.clear()

    def _set_up_account(self, user) -> None:
        """A new account: the tutor calls the learner by name, in the language
        they chose to learn."""
        save_assistant_config(get_assistant_name(), user["name"])
        save_plugin_config("language_tutor", {"mode": user["learning"]})
        run = plugin_fn("run")
        if run is not None:
            run({"action": "set_mode", "mode": user["learning"]})
        fn = plugin_fn("switch_user")
        if fn is not None:
            fn()

    async def signed_out(self, user_id: int) -> None:
        async with self._seat:
            if self.user_id != user_id:
                return
            await self._leave({"type": "signed_out"})
            await asyncio.to_thread(self._switch_files, None)
            self.user_id = None

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

    async def courses(self, request: web.Request) -> web.Response:
        """The course list (/api/catalog) and one course (/api/course?key=).
        Open without an account too; the learner's own progress only with one."""
        user = await self.accounts.user_of(request)
        if user is not None:
            await self.claim(user)
        one = request.path == "/api/course"
        fn = plugin_fn("course_for_ui" if one else "catalog_for_ui")
        if fn is None:
            return web.json_response({"error": "not available"}, status=404)
        try:
            if one:
                value = await asyncio.to_thread(fn, request.query.get("key", ""))
                if user is None and "lessons" in value:
                    value = dict(value, progress=None, current_language=False,
                                 lessons=[dict(l, state="locked", open=False) for l in value["lessons"]])
            else:
                value = await asyncio.to_thread(fn, user is not None)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
        return _json(value)

    async def data(self, request: web.Request) -> web.Response:
        """The account and dictionary pages ask for their data when opened."""
        getter = {"account": "account_for_ui",
                  "dictionary": "dictionary_for_ui",
                  "intensive": "intensive_for_ui"}.get(request.match_info["page"])
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
        old_mode = str(get_plugin_config("language_tutor").get("mode") or "English")
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
        new_mode = str(get_plugin_config("language_tutor").get("mode") or "English")
        if self.live:
            running = self._session_task is not None and not self._session_task.done()
            if new_mode != old_mode and running:
                # Another language: a new lesson from the start, with a clean
                # board, in that language's course.
                self.live.restart()
                return web.json_response({"ok": True})
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
            # No page is open any more (closed, or reloading): the teacher stops.
            if not self.ui.has_clients():
                self._stop_session()
        return ws

    def _on_message(self, data: dict) -> None:
        kind = data.get("type")
        ui, live = self.ui, self.live
        if kind in ("start", "restart"):
            # Start was pressed. A course lesson chosen on the Courses page comes
            # with it, and is applied BEFORE the session is built.
            if kind == "start" and (data.get("track") or data.get("lesson") is not None):
                asyncio.get_running_loop().create_task(self._start_with(data))
                return
            running = self._session_task is not None and not self._session_task.done()
            if running and (kind == "restart" or data.get("fresh")) and live:
                live.restart()
            else:
                self._start_session()
        elif kind == "stop":
            self._stop_session()
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
        elif kind == "language":
            # Another language: its own level, course and progress, and a new
            # lesson in it from the start.
            self._plugin_async("set_language", str(data.get("value") or "English"),
                               report=True, then=self._fresh_language)
        elif kind == "track":
            # Normal lessons or the intensive course: a new conversation in it.
            self._plugin_async("set_track", str(data.get("value") or "normal"), ui,
                               report=True, then=self._fresh_track)
        elif kind == "intensive_lesson":
            try:
                index = int(data.get("index", 0))
            except (TypeError, ValueError):
                index = 0
            self._plugin_async("goto_lesson", index, ui, report=True, then=self._fresh_track)

    def _fresh_topic(self, ok: bool, message: str) -> None:
        """A new topic (or a new scenario for this one, or the current topic
        deleted): a clean board and a new conversation in it, straight away."""
        if not ok or message.startswith("Already") or not self.live:
            return
        if message.startswith("Deleted") and "Back to free talk" not in message:
            return                          # another topic was deleted: nothing changes here
        # A new topic: the lesson stops, and Start begins it in the new topic.
        self._stop_session()

    async def _start_with(self, data: dict) -> None:
        """Start, with the course (or course lesson) chosen on the Courses page."""
        track, lesson = data.get("track"), data.get("lesson")
        try:
            if lesson is not None:
                fn = plugin_fn("goto_lesson")
                if fn is not None:
                    await asyncio.to_thread(fn, int(lesson), self.ui)
            elif track:
                fn = plugin_fn("set_track")
                if fn is not None:
                    await asyncio.to_thread(fn, str(track), self.ui)
        except Exception as e:
            self.ui.write_log(f"ERR: could not open the course - {e}")
        running = self._session_task is not None and not self._session_task.done()
        if running and self.live:
            self.live.restart(new_topic=True)
        else:
            self._start_session()

    def _stop_session(self) -> None:
        """The lesson ends: the teacher is silent until Start is pressed again."""
        running = self._session_task is not None and not self._session_task.done()
        if running and self.live:
            self.live.stop()
            self._session_task.cancel()
        self.ui.send({"type": "stopped"})

    def _fresh_language(self, ok: bool, message: str) -> None:
        # Another language: the lesson stops; Start begins it in the new one.
        if ok and not message.startswith("Already"):
            self._stop_session()

    def _fresh_track(self, ok: bool, message: str) -> None:
        """Another section or course lesson: the lesson stops until Start."""
        if ok and not message.startswith("Already"):
            self._stop_session()

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
    return origin in (f"http://{request.host}", f"https://{request.host}") or origin in DEV_ORIGINS


@web.middleware
async def _no_stale_files(request: web.Request, handler):
    """The page is a handful of small local files: always revalidate them, so
    an update is never half-applied from the browser cache. Next.js's own
    files carry a hash in their name and never change: they are kept."""
    origin = request.headers.get("Origin")
    dev = origin in DEV_ORIGINS and request.path.startswith("/api/")
    if dev and request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)
    if dev:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    if request.path.startswith("/_next/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif not request.path.startswith(("/api/", "/ws")):
        response.headers["Cache-Control"] = "no-cache"
    return response


async def _frontend(request: web.Request) -> web.StreamResponse:
    """A file of the built Next.js page: /courses/ is courses/index.html."""
    root = FRONTEND_DIR.resolve()
    rel = request.match_info.get("tail", "").strip("/")
    target = (root / rel).resolve() if rel else root
    if root not in target.parents and target != root:
        raise web.HTTPNotFound()
    if target.is_dir():
        target = target / "index.html"
    elif not target.exists() and target.with_suffix(".html").exists():
        target = target.with_suffix(".html")
    elif not target.exists() and target.name.startswith("__next.") and target.suffix == ".txt":
        # A segment prefetch: "__next.account.grammar.__PAGE__.txt" is stored
        # as "__next.account/grammar/__PAGE__.txt" - the dots are folders.
        parts = target.name[len("__next."):-len(".txt")].split(".")
        if len(parts) > 1:
            nested = target.parent / ("__next." + parts[0]) / "/".join(parts[1:])
            nested = nested.with_name(nested.name + ".txt")
            if root in nested.resolve().parents:
                target = nested
    if not target.is_file():
        missing = root / "404.html"
        if missing.is_file():
            return web.FileResponse(missing, status=404)
        raise web.HTTPNotFound()
    return web.FileResponse(target)


# Open without an account: signing in, and the courses (without progress).
PUBLIC_API = ("/api/auth/", "/api/catalog", "/api/course")


def _require_account(state: App):
    @web.middleware
    async def middleware(request: web.Request, handler):
        path = request.path
        if path.startswith("/api/auth/") and request.method == "POST" and not _same_origin(request):
            return web.json_response({"ok": False, "error": "origin"}, status=403)
        guarded = path == "/ws" or (path.startswith("/api/") and not path.startswith(PUBLIC_API))
        if guarded and request.method != "OPTIONS":
            user = await state.accounts.user_of(request)
            if user is None:
                return web.json_response({"ok": False, "error": "auth"}, status=401)
            request["user"] = user
            await state.claim(user)
        return await handler(request)
    return middleware


def build_app() -> web.Application:
    state = App()
    app = web.Application(middlewares=[_no_stale_files, _require_account(state)])
    app.on_startup.append(state.accounts.open)
    app.on_startup.append(state.on_startup)
    app.on_cleanup.append(state.accounts.close)
    app.on_cleanup.append(lambda _app: asyncio.to_thread(store.close))
    app.router.add_get("/ws", state.socket)
    app.router.add_get("/api/auth/me", state.accounts.me)
    app.router.add_post("/api/auth/register", state.accounts.register)
    app.router.add_post("/api/auth/login", state.accounts.login)
    app.router.add_post("/api/auth/logout", state.accounts.logout)
    app.router.add_post("/api/key", state.save_key)
    app.router.add_get("/api/settings", state.get_settings)
    app.router.add_post("/api/settings", state.put_settings)
    app.router.add_get("/api/memory", state.get_memory)
    app.router.add_get("/api/keys", state.get_keys)
    app.router.add_post("/api/keys", state.post_keys)
    app.router.add_get("/api/history", state.get_history)
    app.router.add_post("/api/memory/forget", state.forget_memory)
    app.router.add_get("/api/catalog", state.courses)
    app.router.add_get("/api/course", state.courses)
    app.router.add_get("/api/{page}", state.data)
    if FRONTEND_DIR.is_dir():
        app.router.add_get("/{tail:.*}", _frontend)
    else:
        app.router.add_get("/", state.index)
        app.router.add_static("/static/", STATIC_DIR)
    app["state"] = state
    return app


def main(open_browser: bool = True, port: int | None = None) -> None:
    port = port or PORT
    url = f"http://localhost:{port}/"
    print(f"⚙  LangVis - {url}")
    if open_browser:
        webbrowser.open(url)
    web.run_app(build_app(), host=HOST, port=port, print=None)
