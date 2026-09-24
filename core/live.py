"""
core/live.py - the live lesson: one Gemini Live session, driven from the browser.

The browser owns the microphone and the speaker. Its microphone blocks arrive
here (feed_mic), the tutor's voice goes back to it at speaking speed, and
everything the page shows - state, transcript, subtitles, the board - is sent
through `ui` (web/bridge.WebUI).

The session THINKS before the tutor answers. A live voice model normally
replies the instant the learner stops talking, before anything has checked
what they said - so it answers sentences it should have corrected and cannot
tell a real repeat from a new sentence. Here the server decides when a
learner's turn starts and ends (manual activity detection); when they stop,
the tutor's turn is held, the face shows it is thinking, the sentence is heard
and analysed (plugins/language_tutor.gate_audio), and only then is the turn
released - with a [NEXT] note saying exactly what the reply is: "Did you mean
…? Say it.", "Better: … Now you say it.", or the next question.
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import threading
import time
import traceback
from collections import deque
from datetime import datetime
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from core.plugin_loader import discover_plugins
from memory.config_manager import get_voice
from memory.memory_manager import (
    format_memory_for_prompt, load_memory, pop_last_session, save_session_summary,
    search_memory, set_trim_notifier, update_memory,
)

BASE_DIR        = Path(__file__).resolve().parent.parent
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL      = "models/gemini-3.1-flash-live-preview"

# The browser plays whatever it is sent at once, so audio is released at the
# speed it is spoken with this much kept in hand. Enough to ride out a slow
# frame, little enough that Interrupt is heard to stop straight away.
PLAYBACK_LEAD = 0.30              # seconds
RECEIVE_BYTES_PER_SEC = 24000 * 2

ECHO_GUARD = 0.5                  # s after the tutor's voice ends: cutting in still needs a louder voice
ECHO_TAIL = 2.5                   # s after it ends: a sentence starting now is checked for its echo
OPENING_WAIT = 25.0               # s the mic waits at most for the greeting to be spoken
SEND_CHUNK = 4096                 # bytes per audio message when a finished sentence is sent
REPLY_WAIT = 8.0                  # s the mic stays closed while the released reply arrives
GATE_TIMEOUT = 14.0               # s of thinking before the tutor is let answer on its own
ECHO_GAP = 0.9                    # s after the tutor's voice ends: a sentence starting later is the learner


_key_turn = 0      # which key the voice session uses: the next after a spent one


def _get_api_key() -> str:
    from memory.config_manager import get_gemini_keys
    keys = get_gemini_keys()
    if not keys:
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["gemini_api_key"]
    return keys[_key_turn % len(keys)]


def _next_key() -> bool:
    """A key's limit is spent: move to the next one. False if there is none."""
    global _key_turn
    from memory.config_manager import get_gemini_keys
    if len(get_gemini_keys()) < 2:
        return False
    _key_turn += 1
    return True


def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return ("You are a personal language tutor. Teach the learner to speak, "
                "correct their mistakes gently, and keep them talking.")


def plugin_fn(name: str):
    """A function of a loaded plugin, found by asking the plugins rather than by
    importing one by name - a second course plugin only has to define it."""
    for module in list(sys.modules.values()):
        if getattr(module, "__name__", "").startswith("plugins."):
            fn = getattr(module, name, None)
            if callable(fn):
                return fn
    return None


def _plugin_value(name: str, empty):
    fn = plugin_fn(name)
    if fn is None:
        return empty
    try:
        return fn() or empty
    except Exception:
        return empty


_CTRL_RE = re.compile(r"<ctrl\d+>", re.IGNORECASE)
# The tags of the system's notes. Now and then the model reads one out; the
# page and the transcript never show it.
_TAG_RE = re.compile(r"\[(?:NEXT|SKIP|EXPLAIN|FLUENCY|MISHEARD|BOARD|LESSON_START|TUTOR_[A-Z_]+)\]\s*")


def _clean_transcript(text: str) -> str:
    text = _CTRL_RE.sub("", text)
    text = _TAG_RE.sub("", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", text)
    return text.strip()


# Closing quotes and brackets can trail a question mark.
_QUESTION_END_RE = re.compile(r"[?？؟]\s*[\"'»”’\)\]]*\s*$")

# A tutor does not only hand the floor over with questions. "Say it." "Now you
# try." "Repeat that, please." all mean the same thing: the next voice in the
# room is supposed to be the learner's. Anything injected into that silence is
# read by the model as the learner's reply, and it answers itself.
_FLOOR_CUES = (
    "say it", "say that", "say this", "now you", "you say", "repeat",
    "your turn", "try again", "try it", "tell me", "go ahead", "one more time",
)


def _holds_floor(text: str) -> bool:
    """True if the tutor's turn was waiting for the learner to speak."""
    low = (text or "").lower()
    if _QUESTION_END_RE.search(text or ""):
        return True
    return any(cue in low[-160:] for cue in _FLOOR_CUES)


TOOL_DECLARATIONS = [
    {
        "name": "save_memory",
        "description": (
            "Save a personal fact about the learner so lessons can use it: name, "
            "job, city, family, hobbies, interests, plans, why they are learning "
            "the language. Call it silently - never announce it. Do NOT save "
            "their grammar mistakes or their level; the tutor plugin tracks those. "
            "Values must be in English."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity - name, age, city, job, native language | "
                        "preferences - likes, hobbies, favourite things | "
                        "projects - work, studies, what they are building | "
                        "relationships - family, friends, colleagues | "
                        "wishes - goals, plans, dreams | notes - anything else"
                    ),
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. job, favourite_food)"},
                "value": {"type": "STRING", "description": "Concise value in English"},
            },
            "required": ["category", "key", "value"],
        },
    },
    {
        "name": "recall_memory",
        "description": (
            "Look up something you were told about the learner but cannot see in "
            "your memory block (the keys listed under [ALSO REMEMBERED]). Call it "
            "before saying you do not remember. Leave the query empty to list "
            "everything. Instant local search."
        ),
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING",
                          "description": "A name, topic or category to search for."},
            },
            "required": [],
        },
    },
]


class _ReconnectSignal(Exception):
    """Raised inside the session TaskGroup to force a clean, voluntary reconnect
    (e.g. a new voice - the voice is fixed at connect time). `keep_context`
    says whether the stored resumption handle is replayed."""

    def __init__(self, keep_context: bool = True):
        super().__init__()
        self.keep_context = keep_context


def _describe(exc: BaseException) -> str:
    """Type and message of an exception - and of every one inside a group, which
    is how a TaskGroup reports the task that actually failed."""
    if isinstance(exc, BaseExceptionGroup):
        return " | ".join(_describe(sub) for sub in exc.exceptions)
    return f"{type(exc).__name__}: {exc}"


def _is_reconnect_signal(exc: BaseException) -> bool:
    if isinstance(exc, _ReconnectSignal):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(_is_reconnect_signal(sub) for sub in exc.exceptions)
    return False


def _keep_context_of(exc: BaseException) -> bool:
    """Read `keep_context` off a reconnect signal, unwrapping the TaskGroup's
    group. Defaults to True: an unexpected shape must not wipe the lesson."""
    if isinstance(exc, _ReconnectSignal):
        return getattr(exc, "keep_context", True)
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            if _is_reconnect_signal(sub):
                return _keep_context_of(sub)
    return True


class _Vad:
    """Where a learner's sentence starts and ends, from the loudness of 64 ms
    blocks. The browser already cleans the signal (echo cancellation, noise
    suppression, gain), so a plain level threshold is enough. A learner pauses
    to find words, so a sentence ends only after a real silence."""

    START_LEVEL = 550         # RMS of int16 samples
    STOP_LEVEL = 380
    START_BLOCKS = 2          # this many loud blocks in a row start a sentence (~130 ms)
    # Cutting in while the tutor speaks: its own voice is mostly cancelled by
    # the browser, but what is left must not count as the learner.
    BARGE_LEVEL = 1300
    BARGE_BLOCKS = 6          # ~380 ms of clear speech
    END_SILENCE = 1.1         # seconds of quiet that end it
    MAX_SECONDS = 30.0
    BLOCK_SECONDS = 1024 / 16000
    PREROLL = 5               # quiet blocks kept from before the start (~320 ms)

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.active = False
        self._loud = 0
        self._quiet = 0.0
        self._before: deque[bytes] = deque(maxlen=self.PREROLL)
        self._chunks: list[bytes] = []
        self._speech = 0.0

    def feed(self, samples: np.ndarray, barge: bool = False) -> str | None:
        """'start', 'end' or None. `barge`: the tutor is speaking, so starting
        takes a louder, longer voice."""
        x = samples.astype(np.float32)
        level = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
        block = samples.tobytes()
        if not self.active:
            start_level = self.BARGE_LEVEL if barge else self.START_LEVEL
            need = self.BARGE_BLOCKS if barge else self.START_BLOCKS
            self._loud = self._loud + 1 if level >= start_level else 0
            if self._loud >= need:
                self.active = True
                self._chunks = list(self._before) + [block]
                self._quiet = 0.0
                self._speech = self.BLOCK_SECONDS * self._loud
                return "start"
            self._before.append(block)
            return None
        self._chunks.append(block)
        if level < self.STOP_LEVEL:
            self._quiet += self.BLOCK_SECONDS
        else:
            self._quiet = 0.0
            self._speech += self.BLOCK_SECONDS
        total = len(self._chunks) * self.BLOCK_SECONDS
        if self._quiet >= self.END_SILENCE or total >= self.MAX_SECONDS:
            return "end"
        return None

    def heard(self) -> list[bytes]:
        """Everything heard so far, from just before the start."""
        return list(self._chunks)

    def take(self) -> tuple[bytes, float]:
        """The finished sentence and how much of it was actual speech."""
        data, speech = b"".join(self._chunks), self._speech
        self.reset()
        return data, speech


class LiveSession:
    def __init__(self, ui):
        self.ui                = ui
        self._asst_name        = "LangVis"    # updated each session from config
        self.session           = None
        self.audio_in_queue    = None         # the tutor's voice, on its way out
        self.out_queue         = None         # the learner's voice and markers, on their way in
        self._loop             = None
        self._is_speaking      = False
        self._speaking_lock    = threading.Lock()   # the tutor thread reads it too
        self._interrupted      = False   # True while draining audio after an interrupt
        self._reconnect_event: asyncio.Event | None = None
        self._reconnect_keep   = True
        self._reconnect_reason = ""
        self._conn_backoff     = 3

        # The server issues a resumption handle every few seconds; keeping it
        # means a dropped connection does not restart the lesson. RAM only: a
        # fresh launch begins a new lesson, which also writes the summary.
        self._resume_handle: str | None = None
        self._turn_done_event: asyncio.Event | None = None
        self._lesson_started   = False
        self._new_topic        = False   # the next opening starts a topic just chosen
        self._last_user_speech = time.monotonic()
        self._awaiting_answer  = False   # the floor belongs to the learner
        self._session_log: list[str] = []

        # Thinking before answering.
        self._vad = _Vad()
        self._gate_task: asyncio.Task | None = None
        self._gated_turn = False       # this turn was already analysed by the gate
        self._reply_until = 0.0        # the tutor's reply is on its way: mic closed
        self._quiet_until = 0.0        # the tail of the tutor's voice may still be playing
        self._play_until = 0.0
        self._open_at = 0.0            # the greeting is on its way: mic closed until then
        self._you_logged = False       # the learner's line of this turn is already written
        self._utt_barge = False        # the sentence being heard began over (or just after) the tutor's voice
        self._utt_gap = -1.0           # s between the tutor's voice ending and the sentence starting (-1: over it)
        self._speech_end = 0.0
        self._echo_until = 0.0         # the speakers may still be playing the tutor's last words
        self._tutor_text = ""          # what the tutor said lately - to recognise its echo
        self._turn_spoke = False       # the tutor's current turn has already made a sound
        self._drop_rest = False        # a tool call ended a spoken turn: the rest is not said

        # The tutor only ever speaks when it was asked to: after the learner's
        # sentence, a system note that wants a reply, or the lesson opening. A
        # turn nobody asked for - "I still haven't heard from you" into a
        # silence - is dropped before a word of it is heard.
        self._reply_pending = False
        self._turn_state: str | None = None     # None · "ok" · "drop"

        self._plugin_registry = discover_plugins(
            plugins_dir=BASE_DIR / "plugins",
            core_tool_names={t["name"] for t in TOOL_DECLARATIONS},
            logger=lambda msg: print(f"[Plugins] {msg}"),
        )
        ui.request_say           = self.plugin_say
        ui.request_say_when_idle = self.plugin_say_when_idle
        ui.request_context       = self.plugin_context

    # ── What the page asks for ───────────────────────────────────────────────

    def lesson_status(self) -> dict:
        return _plugin_value("status_for_ui", {})

    def syllabus(self) -> list:
        return _plugin_value("syllabus_for_ui", [])

    def coaching(self) -> dict:
        return _plugin_value("coaching_for_ui", {})

    def change_language(self, name: str) -> None:
        """The language is baked into the whole system prompt, so a new one
        rebuilds the session from scratch."""
        switch = plugin_fn("set_language")
        if switch is None:
            return
        try:
            ok, message = switch(name)
            self.ui.write_log(f"SYS: {message}")
            if ok and "Already" not in message:
                self.request_reconnect(keep_context=False, reason="new language")
        except Exception as e:
            self.ui.write_log(f"ERR: language switch failed - {e}")

    # ── Speech channels for plugins ──────────────────────────────────────────

    def _expect_reply(self) -> None:
        self._reply_pending = True

    def _send_turn(self, text: str, complete: bool) -> None:
        loop = self._loop
        if not loop or not self.session:
            return
        if complete:
            self._expect_reply()

        async def _send():
            try:
                await self.session.send_client_content(
                    turns={"role": "user", "parts": [{"text": text}]}, turn_complete=complete)
            except Exception as e:
                print(f"[PluginSay] {e}")

        try:
            asyncio.run_coroutine_threadsafe(_send(), loop)
        except Exception as e:
            print(f"[PluginSay] {e}")

    def plugin_say(self, instruction: str) -> None:
        """Thread-safe: have the tutor say something now."""
        self._send_turn(instruction, complete=True)

    def plugin_context(self, text: str) -> None:
        """Thread-safe: add a note to the conversation WITHOUT asking for a
        reply (turn_complete=False) - an updated plan, what the board shows.
        The tutor reads it on its next turn; it never speaks because of it."""
        self._send_turn(text, complete=False)

    def plugin_say_when_idle(self, instruction: str,
                             quiet_for: float = 1.2,
                             max_wait: float = 45.0,
                             user_action: bool = False) -> None:
        """Same channel, but it waits for a gap first: nothing being spoken,
        nothing queued, the learner quiet, and the floor not theirs. If that
        moment never comes within max_wait the note is dropped - a note spoken
        into the learner's turn makes the tutor look like it answers itself."""
        loop = getattr(self, "_loop", None)
        if not loop or not self.session:
            return

        async def _wait_then_say():
            deadline = time.monotonic() + max_wait
            while time.monotonic() < deadline:
                with self._speaking_lock:
                    speaking = self._is_speaking
                queued = bool(self.audio_in_queue and not self.audio_in_queue.empty())
                quiet = (time.monotonic() - self._last_user_speech) >= quiet_for
                busy = self._vad.active or (self._gate_task is not None and not self._gate_task.done())
                if user_action:
                    # The learner pressed something (Skip, a word on the board):
                    # they are waiting for it, so only the tutor's own voice
                    # and a sentence being heard are waited out.
                    if not speaking and not queued and not busy:
                        break
                elif not speaking and not queued and quiet and not busy and not self._awaiting_answer:
                    break
                await asyncio.sleep(0.4)
            else:
                print("[PluginSay] the floor stayed with the learner - note dropped")
                return
            try:
                self._expect_reply()
                await self.session.send_client_content(
                    turns={"role": "user", "parts": [{"text": instruction}]}, turn_complete=True)
            except Exception as e:
                print(f"[PluginSay] {e}")

        try:
            asyncio.run_coroutine_threadsafe(_wait_then_say(), loop)
        except Exception as e:
            print(f"[PluginSay] {e}")

    # ── Reconnect plumbing ───────────────────────────────────────────────────

    def request_reconnect(self, keep_context: bool = True, reason: str = ""):
        """Thread-safe: ask the run loop to tear down and rebuild the session."""
        self._reconnect_keep   = keep_context
        self._reconnect_reason = reason
        loop, ev = self._loop, self._reconnect_event
        if loop and ev is not None:
            loop.call_soon_threadsafe(ev.set)

    async def _watch_reconnect(self):
        assert self._reconnect_event is not None
        await self._reconnect_event.wait()
        self._reconnect_event.clear()
        keep = self._reconnect_keep
        self.ui.write_log(f"SYS: Applying {self._reconnect_reason or 'settings'} - reconnecting"
                          + ("..." if keep else " (starting a fresh lesson)..."))
        raise _ReconnectSignal(keep_context=keep)

    # ── The learner speaks ───────────────────────────────────────────────────

    def set_speaking(self, value: bool):
        with self._speaking_lock:
            was = self._is_speaking
            self._is_speaking = value
        if was and not value:
            self._quiet_until = time.monotonic() + ECHO_GUARD
            # The browser plays a little behind the server, and the room rings:
            # its last words can reach the mic after the server thinks it stopped.
            self._echo_until = time.monotonic() + ECHO_TAIL
            self._speech_end = time.monotonic()
            self._open_at = 0.0             # the greeting (or any turn) is over
        if value:
            self._reply_until = 0.0
            self.ui.set_state("SPEAKING")
        elif not self.ui.muted:
            self.ui.set_state("LISTENING")

    def feed_mic(self, pcm16k: bytes) -> None:
        """One block of 16 kHz mono int16 from the browser. Runs on the loop.

        A sentence is collected here and sent to the model only once it is
        finished and checked - so a cough, a chair or the tail of the tutor's
        own voice never reaches it as "the learner said something".

        The learner may cut in while the tutor speaks - but only with a clear,
        louder voice, and a sentence that began over the tutor's voice is
        checked against what the tutor was saying: with speakers instead of
        headphones its own voice comes back through the mic, and anything that
        reaches the model as "the learner" makes it answer itself. The opening
        greeting is never cut: the mic waits for it."""
        if not pcm16k or self.out_queue is None or not self.session:
            return
        with self._speaking_lock:
            speaking = self._is_speaking
        now = time.monotonic()
        closed = (self.ui.muted or now < self._open_at or now < self._reply_until
                  or (self._gate_task is not None and not self._gate_task.done()))
        if closed:
            self._vad.reset()               # muted mid-sentence: drop it cleanly
            return

        barge = speaking or now < self._quiet_until
        event = self._vad.feed(np.frombuffer(pcm16k, dtype=np.int16), barge=barge)
        if event == "start":
            self._utt_barge = barge or now < self._echo_until
            self._utt_gap = -1.0 if speaking else now - self._speech_end
            if speaking:
                self.interrupt()
                self.ui.write_log("SYS: You cut in - the tutor stopped to listen.")
            self.ui.hold_live = False
            self._last_user_speech = now
            self._awaiting_answer = False
            self.ui.send({"type": "hearing", "value": True})
            return
        if event == "end":
            self.ui.send({"type": "hearing", "value": False})
            utterance, seconds = self._vad.take()
            self._gate_task = asyncio.get_running_loop().create_task(
                self._think_then_answer(utterance, seconds))

    def _queue(self, msg: dict) -> None:
        """Audio, activity markers and notes share one queue, so they reach the
        model in the order they happened."""
        try:
            self.out_queue.put_nowait(msg)
        except asyncio.QueueFull:
            pass

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            if "activity" in msg:
                if msg["activity"] == "start":
                    await self.session.send_realtime_input(activity_start=types.ActivityStart())
                else:
                    await self.session.send_realtime_input(activity_end=types.ActivityEnd())
            elif "note" in msg:
                await self.session.send_client_content(
                    turns={"role": "user", "parts": [{"text": msg["note"]}]}, turn_complete=False)
            else:
                await self.session.send_realtime_input(
                    audio=types.Blob(data=msg["data"], mime_type="audio/pcm;rate=16000"))

    async def _think_then_answer(self, utterance: bytes, seconds: float) -> None:
        """Hold the tutor's turn while the sentence is checked, then release it
        with the reply decided."""
        gate = plugin_fn("gate_audio")
        note, handled = None, False
        if seconds < 0.3:
            self.ui.set_state("LISTENING")
            return                          # a click or a breath, not a sentence
        if gate is not None:
            self.ui.set_state("THINKING")
            try:
                # The echo is judged inside the gate, BEFORE the lesson moves on;
                # past the deadline the gate changes nothing.
                decided = await asyncio.wait_for(
                    asyncio.to_thread(gate, utterance, seconds, self.ui, self._echo_of,
                                      time.monotonic() + GATE_TIMEOUT - 0.5),
                    timeout=GATE_TIMEOUT) or {}
                if decided.get("drop"):
                    # Nothing was said - noise, or the tutor's own voice.
                    self.ui.set_state("LISTENING")
                    self.ui.send({"type": "hearing", "value": None})
                    return
                note = decided.get("note")
                handled = bool(decided.get("handled")) or note is not None
                heard = str(decided.get("text") or "").strip()
                if heard and not decided.get("handled") and self._echo_of(heard):
                    # It began over the tutor's voice and is the tutor's own
                    # words: its echo, not the learner.
                    print(f"[LangVis] echo dropped: {heard[:60]}")
                    self.ui.set_state("LISTENING")
                    self.ui.send({"type": "hearing", "value": None})
                    return
                if heard:
                    # The transcript gets the sentence as the analyser heard it,
                    # now - before the reply. The model's own transcription of
                    # it comes late, after the reply, or not at all.
                    self.ui.write_log(f"You: {heard}")
                    self._session_log.append(f"Learner: {heard}")
                    self._you_logged = True
            except asyncio.TimeoutError:
                print("[LangVis] thinking took too long - the tutor answers on its own")
            except Exception as e:
                print(f"[LangVis] thinking failed: {e}")
        self._gated_turn = handled
        self.ui.hold_live = handled         # the board already shows the sentence
        # The whole sentence goes to the model at once, with the decided reply.
        self._queue({"activity": "start"})
        for i in range(0, len(utterance), SEND_CHUNK):
            self._queue({"data": utterance[i:i + SEND_CHUNK]})
        if note:
            self._queue({"note": note})
        self._expect_reply()
        self._queue({"activity": "end"})
        self._reply_until = time.monotonic() + REPLY_WAIT

    def _echo_of(self, heard: str) -> bool:
        """The tutor's own voice coming back: a sentence that began over its
        voice, or in the first moment after it, made of its words. A learner
        repeating "Say it: prosím" starts later - and says the same words."""
        if not self._utt_barge or self._utt_gap >= ECHO_GAP:
            return False
        return self._is_echo(heard)

    def _is_echo(self, heard: str) -> bool:
        """Nearly every word of it was in what the tutor was just saying."""
        said = re.findall(r"[^\W\d_']+", heard.lower())
        tutor = set(re.findall(r"[^\W\d_']+", self._tutor_text.lower()))
        if not said or not tutor:
            return False
        return sum(w in tutor for w in said) / len(said) >= 0.8

    async def typed(self, text: str) -> None:
        """A typed sentence goes through the same thinking as a spoken one."""
        gate = plugin_fn("gate_text")
        note = None
        if gate is not None:
            self.ui.set_state("THINKING")
            try:
                decided = await asyncio.wait_for(asyncio.to_thread(gate, text, self.ui),
                                                 timeout=GATE_TIMEOUT)
                note = (decided or {}).get("note")
            except Exception as e:
                print(f"[LangVis] thinking failed: {e}")
        if not self.session:
            return
        if note:
            await self.session.send_client_content(
                turns={"role": "user", "parts": [{"text": note}]}, turn_complete=False)
        self._expect_reply()
        await self.session.send_client_content(
            turns={"role": "user", "parts": [{"text": text}]}, turn_complete=True)
        if gate is None:
            self._plugin_registry.observe(text, player=self.ui)

    def _observe_turn(self, text: str) -> None:
        """A learner turn is complete. If the gate already analysed it, nothing
        is counted twice; otherwise it goes to the tutor's analyser."""
        if self._gated_turn:
            self._gated_turn = False
            self.ui.hold_live = False
            return
        self._plugin_registry.observe(text, player=self.ui)

    def restart(self, new_topic: bool = False) -> None:
        """Start the lesson again from nothing: a new session with no memory of
        this conversation, a new greeting, an empty board. Progress is kept.
        `new_topic`: the learner has just picked a topic - the opening starts
        it (and its scenario) instead of recapping the last lesson."""
        reset = plugin_fn("reset_lesson")
        if reset is not None:
            reset()
        with self._speaking_lock:
            speaking = self._is_speaking
        if speaking or (self.audio_in_queue and not self.audio_in_queue.empty()):
            self.interrupt()                 # the old conversation stops mid-word
        self._lesson_started = False
        self._new_topic = new_topic
        self._gated_turn = False
        self._vad.reset()
        self.ui.reset()
        self.request_reconnect(keep_context=False, reason="a fresh start")

    def interrupt(self) -> None:
        """Stop the tutor mid-speech: drop its queued voice, let the learner talk."""
        self._interrupted = True
        q = self.audio_in_queue
        while q:
            try:
                q.get_nowait()
            except Exception:
                break
        self._play_until = 0.0
        self.set_speaking(False)
        if self._turn_done_event:
            self._turn_done_event.clear()
        self.ui.send({"type": "flush"})

    # ── The session ──────────────────────────────────────────────────────────

    def _build_config(self) -> types.LiveConnectConfig:
        try:
            _cfg = json.loads(API_CONFIG_PATH.read_text(encoding="utf-8"))
            self._asst_name = (_cfg.get("assistant_name") or "LangVis").strip()
            _user_name = (_cfg.get("user_name") or "").strip()
        except Exception:
            self._asst_name = "LangVis"
            _user_name = ""

        now = datetime.now()
        parts = [
            f"[CURRENT DATE & TIME]\nRight now it is: {now.strftime('%A, %B %d, %Y - %I:%M %p')}\n\n",
            f"[IDENTITY]\nYour name is {self._asst_name}. Always refer to yourself as "
            f"{self._asst_name}.\n"
            + (f"Call the learner '{_user_name}'.\n\n" if _user_name
               else "Use the learner's first name if you know it.\n\n"),
        ]
        mem_str = format_memory_for_prompt(load_memory())
        if mem_str:
            parts.append(mem_str)
        # The course itself: level, topic, current unit, focus skills, how to speak.
        parts.extend(self._plugin_registry.prompt_blocks())
        parts.append(_load_system_prompt())

        return types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            output_audio_transcription={},
            input_audio_transcription={},
            system_instruction="\n".join(parts),
            tools=[{"function_declarations": (
                TOOL_DECLARATIONS + self._plugin_registry.get_tool_declarations())}],
            session_resumption=types.SessionResumptionConfig(handle=self._resume_handle),
            # Sliding-window compression: a lesson can run for hours without the
            # session dying from a full context window.
            context_window_compression=types.ContextWindowCompressionConfig(
                sliding_window=types.SlidingWindow()),
            speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=get_voice()))),
            # The server decides when the learner's turn ends - see feed_mic.
            realtime_input_config=types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(disabled=True)),
        )

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        print(f"[LangVis] 🔧 {name}  {args}")

        if name == "save_memory":
            key, value = args.get("key", ""), args.get("value", "")
            if key and value:
                update_memory({args.get("category", "notes"): {key: {"value": value}}})
                print(f"[Memory] 💾 {key} = {value}")
            return types.FunctionResponse(id=fc.id, name=name,
                                          response={"result": "ok", "silent": True})

        self.ui.set_state("THINKING")
        result = "Done."
        try:
            if name == "recall_memory":
                result = search_memory(args.get("query", ""), limit=8)
            elif self._plugin_registry.has(name):
                r = await asyncio.to_thread(self._plugin_registry.run, name, args,
                                            player=self.ui, session_memory=None)
                result = r or "Done."
            else:
                result = f"Unknown tool: {name}"
        except Exception as e:
            result = f"Tool '{name}' failed: {e}"
            traceback.print_exc()
            self.ui.write_log(f"ERR: {name} - {str(e)[:120]}")
        if not self.ui.muted:
            self.ui.set_state("LISTENING")
        print(f"[LangVis] 📤 {name} → {' '.join(str(result).split())[:80]}")
        return types.FunctionResponse(id=fc.id, name=name, response={"result": result})

    async def _receive(self):
        out_buf, in_buf = [], []
        while True:
            async for response in self.session.receive():

                # `resumable` goes false while a turn is mid-flight; only
                # resumable handles are kept.
                sru = getattr(response, "session_resumption_update", None)
                if sru is not None and getattr(sru, "resumable", False) \
                        and getattr(sru, "new_handle", None):
                    self._resume_handle = sru.new_handle

                # GoAway: leave on our own terms, with the handle armed.
                if response.go_away is not None:
                    print(f"[LangVis] ⚠️  Server GoAway - reconnecting")
                    self.request_reconnect(keep_context=True, reason="server session limit")

                sc = response.server_content
                starts = bool(response.data) or bool(sc and sc.output_transcription
                                                     and sc.output_transcription.text)
                if starts and self._turn_state is None:
                    # A new turn of the tutor's: was it asked for?
                    self._turn_state = "ok" if self._reply_pending else "drop"
                    self._reply_pending = False
                    if self._turn_state == "drop":
                        print("[LangVis] 🤐 An unasked turn was dropped - the tutor waits")
                silent = self._turn_state == "drop"

                silent = silent or self._drop_rest
                if response.data and not silent:
                    self._turn_spoke = True
                if response.data and not self._interrupted and not silent:
                    if self._turn_done_event and self._turn_done_event.is_set():
                        self._turn_done_event.clear()
                    # ~50 ms slices so interrupt() stops audio quickly.
                    for i in range(0, len(response.data), 2400):
                        self.audio_in_queue.put_nowait(response.data[i:i + 2400])

                if sc:
                    if sc.output_transcription and sc.output_transcription.text and not silent:
                        txt = _clean_transcript(sc.output_transcription.text)
                        if txt and txt != (out_buf[-1] if out_buf else ""):
                            out_buf.append(txt)
                            self._tutor_text = " ".join(out_buf)
                            # The tutor's words, as it says them, in its bubble -
                            # not the rest of a turn the learner cut off.
                            if not self._interrupted:
                                self.ui.send({"type": "tutor_words", "text": " ".join(out_buf)})

                    if sc.input_transcription and sc.input_transcription.text:
                        txt = _clean_transcript(sc.input_transcription.text)
                        if txt:
                            in_buf.append(txt)
                            self._last_user_speech = time.monotonic()
                            self._awaiting_answer = False
                            self.ui.set_live_sentence(" ".join(in_buf))

                    if sc.turn_complete:
                        self._turn_state = None
                        self._turn_spoke = False
                        self._drop_rest = False
                        if self._turn_done_event:
                            self._turn_done_event.set()
                        if self._interrupted:
                            self._interrupted = False
                            in_buf, out_buf = [], []
                            continue
                        full_in = " ".join(in_buf).strip()
                        if full_in:
                            self.ui.set_live_sentence(full_in, final=True)
                            if not self._you_logged:
                                self.ui.write_log(f"You: {full_in}")
                                self._session_log.append(f"Learner: {full_in}")
                            self._observe_turn(full_in)
                        elif self._gated_turn:
                            self._gated_turn = False
                            self.ui.hold_live = False
                        self._you_logged = False
                        in_buf = []
                        full_out = " ".join(out_buf).strip()
                        if full_out:
                            # A turn ending on a question holds the floor for
                            # the learner - see plugin_say_when_idle.
                            self._awaiting_answer = _holds_floor(full_out)
                            self.ui.write_log(f"{self._asst_name}: {full_out}")
                            self._session_log.append(f"{self._asst_name}: {full_out}")
                            self.ui.send({"type": "tutor_words", "text": full_out, "final": True})
                            said = plugin_fn("tutor_said")
                            if said is not None:
                                asyncio.create_task(asyncio.to_thread(said, full_out, self.ui))
                            if "?" in full_out[-160:]:
                                # A question: answers the learner could give, on the board.
                                answers = plugin_fn("answers_for")
                                if answers is not None:
                                    asyncio.create_task(asyncio.to_thread(answers, full_out, self.ui))
                        out_buf = []

                if response.tool_call:
                    responses = [await self._execute_tool(fc)
                                 for fc in response.tool_call.function_calls]
                    if self._turn_spoke:
                        # The turn was already said - "save this fact" at its
                        # end. Whatever the model adds after the tool's answer
                        # is a second turn nobody asked for: the tutor would
                        # talk on by itself.
                        self._drop_rest = True
                    else:
                        self._expect_reply()      # the answer comes after the tool
                    await self.session.send_tool_response(function_responses=responses)

    async def _play(self):
        """Release the tutor's voice to the browser at speaking speed, so the
        server knows when it is speaking and Interrupt can stop it."""
        self._play_until = 0.0
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    if (self._turn_done_event and self._turn_done_event.is_set()
                            and self.audio_in_queue.empty()
                            and time.monotonic() >= self._play_until):
                        self.set_speaking(False)
                        self._turn_done_event.clear()
                    continue

                self.set_speaking(True)
                batch = bytearray(chunk)
                while len(batch) < 9600:
                    try:
                        batch.extend(self.audio_in_queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                now = time.monotonic()
                ahead = self._play_until - now
                if ahead > PLAYBACK_LEAD:
                    await asyncio.sleep(ahead - PLAYBACK_LEAD)
                    if self._interrupted:
                        continue            # Interrupt landed while we waited
                    now = time.monotonic()
                self._play_until = max(self._play_until, now) + len(batch) / RECEIVE_BYTES_PER_SEC
                self.ui.send_audio(bytes(batch))
        finally:
            self.set_speaking(False)

    async def _start_lesson(self) -> None:
        """One message that opens the lesson. Everything it needs is already in
        the system prompt, so the tutor starts talking at once."""
        await asyncio.sleep(0.4)
        if not self.session:
            return
        identity = load_memory().get("identity", {})
        entry = identity.get("name", {})
        name = (entry.get("value", "") if isinstance(entry, dict) else str(entry)).strip()

        new_topic, self._new_topic = self._new_topic, False
        # A topic just chosen is a new conversation: no recap of the last one.
        language = _plugin_value("language_name", "English")
        last = None if new_topic else await asyncio.to_thread(pop_last_session, language)
        recap = ""
        if last:
            try:
                days = (datetime.now() - datetime.strptime(last["date"], "%Y-%m-%d")).days
                when = "earlier today" if days == 0 else ("yesterday" if days == 1
                                                          else f"{days} days ago")
            except Exception:
                when = "last time"
            recap = (f" In one short sentence, remind them what you practised {when}: "
                     f"{last['summary']}")
        if new_topic:
            prompt = (
                "[LESSON_START] The learner has just chosen the topic in your [LESSON PLAN]: "
                "a new conversation starts now, about that topic only. If the plan has THE "
                "LEARNER'S SCENARIO, start it exactly as it says, in your role; otherwise "
                "name the topic in one short sentence. Then ask ONE first question in it. "
                "Two or three short sentences in total. Do not call any tools. Do not read "
                "this instruction aloud and never mention the plan itself."
            )
        else:
            prompt = (
                "[LESSON_START] Begin today's lesson now, following the [LESSON PLAN] in "
                "your instructions. Greet the learner warmly"
                + (f" by name ({name})" if name else "")
                + " in the language you are teaching, at their level." + recap
                + " Then ask ONE easy question in the current topic. Two or three short "
                  "sentences in total. Do not call any tools. Do not read this "
                  "instruction aloud and never mention the plan itself."
            )
        # A beginner pauses between words: the sentence ends after a longer quiet.
        pause = plugin_fn("end_silence")
        if pause is not None:
            try:
                self._vad.END_SILENCE = float(await asyncio.to_thread(pause))
            except Exception:
                pass
        # A topic not taught yet opens with its taught part: words, a dialogue,
        # sentence frames - the tutor teaches before it asks.
        opening = plugin_fn("opening_note")
        if opening is not None:
            try:
                note = await asyncio.to_thread(opening, self.ui)
                if note:
                    prompt = note
            except Exception as e:
                print(f"[LangVis] opening lesson failed: {e}")
        if not self.session:
            return
        self._expect_reply()
        await self.session.send_client_content(
            turns={"role": "user", "parts": [{"text": prompt}]}, turn_complete=True)
        self.ui.write_log("SYS: Lesson started.")

    async def _save_session_summary(self) -> None:
        """One or two sentences about this lesson, for the next one to open on."""
        log = self._session_log
        if len(log) < 3:
            return
        self._session_log = []
        prompt = ("Below is a language lesson between a tutor and a learner. In ONE or TWO "
                  "short English sentences, say what was practised (topic and grammar) and "
                  "the main mistake to work on next time. No preamble.\n\n" + "\n".join(log[-40:]))
        try:
            client = genai.Client(api_key=_get_api_key())
            resp = await asyncio.to_thread(client.models.generate_content,
                                           model="gemini-flash-lite-latest", contents=prompt)
            summary = (getattr(resp, "text", "") or "").strip()
            if summary:
                save_session_summary(summary[:280], _plugin_value("language_name", "English"))
        except Exception as e:
            print(f"[Memory] ⚠️ Lesson summary failed: {e}")

    async def run(self):
        self._loop = asyncio.get_running_loop()
        self._reconnect_event = asyncio.Event()
        set_trim_notifier(self.ui.write_log)

        while True:
            resumed = self._resume_handle is not None
            try:
                print("[LangVis] Connecting...")
                self.ui.set_state("THINKING")
                config = self._build_config()
                client = genai.Client(api_key=_get_api_key(),
                                      http_options={"api_version": "v1beta"})
                async with (
                    client.aio.live.connect(model=LIVE_MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session          = session
                    self.audio_in_queue   = asyncio.Queue()
                    self.out_queue        = asyncio.Queue(maxsize=400)
                    self._turn_done_event = asyncio.Event()
                    self._interrupted     = False
                    self._vad.reset()
                    self._reply_pending = False
                    self._turn_state = None
                    print("[LangVis] Connected.")
                    # A new lesson: the tutor speaks first, so it is not the
                    # learner's turn yet.
                    self.ui.set_state("THINKING" if not self._lesson_started else "LISTENING")
                    self.ui.write_log("SYS: Reconnected - lesson restored." if resumed
                                      else "SYS: Tutor online.")
                    self._reconnect_event.clear()   # ignore requests from before this session
                    tg.create_task(self._watch_reconnect())
                    tg.create_task(self._send_realtime())
                    tg.create_task(self._receive())
                    tg.create_task(self._play())
                    if not self._lesson_started:
                        self._lesson_started = True
                        # The tutor speaks first; the mic waits for the greeting.
                        self._open_at = time.monotonic() + OPENING_WAIT
                        tg.create_task(self._start_lesson())
                print("[LangVis] Session ended without an error")

            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException as e:
                # TaskGroup wraps child exceptions in a BaseExceptionGroup,
                # which `except Exception` would miss.
                if _is_reconnect_signal(e):
                    print(f"[LangVis] Reconnect: {self._reconnect_reason or 'requested'}")
                    if not _keep_context_of(e):
                        self._resume_handle = None
                    self._conn_backoff = 0
                    continue
                err = _describe(e)
                print(f"[LangVis] Session ended: {err[:400]}")
                if resumed and (any(k in err.lower() for k in ("resum", "handle"))
                                or "INVALID_ARGUMENT" in err or "NOT_FOUND" in err):
                    # A handle the server will not accept: start fresh, or the
                    # dead handle is replayed forever.
                    self.ui.write_log("SYS: Could not restore the lesson - starting fresh.")
                    self._resume_handle = None
                    self._conn_backoff = 0
                    continue
                if ("RESOURCE_EXHAUSTED" in err or "429" in err or "quota" in err.lower()) and _next_key():
                    self.ui.write_log("SYS: This Gemini key reached its limit - switching to the next key.")
                    self._conn_backoff = 1
                    continue
                if "ConnectionClosed" in err:
                    self._conn_backoff = 1
                    continue
                traceback.print_exc()
                if "API key not valid" in err or "1007" in err:
                    self.ui.write_log("ERR: API key invalid - please enter it again.")
                    self.ui.set_state("SLEEPING")
                    self.ui.prompt_reconfig()
                    while not self.ui.key_ready:
                        await asyncio.sleep(1)
                    self._conn_backoff = 1
                elif any(k in err for k in ("TimeoutError", "timed out", "getaddrinfo",
                                            "CancelledError", "ConnectionRefusedError",
                                            "OSError", "Cannot connect")):
                    self._conn_backoff = min(max(self._conn_backoff, 3) * 2, 60)
                    self.ui.write_log(f"NET: Connection failed - retrying in "
                                      f"{self._conn_backoff}s. (a VPN may be required)")
                else:
                    self._conn_backoff = 3
            finally:
                self.session = None
                if len(self._session_log) >= 3:
                    asyncio.create_task(self._save_session_summary())

            self.set_speaking(False)
            self.ui.set_state("SLEEPING")
            await asyncio.sleep(self._conn_backoff)
