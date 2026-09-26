"""
tutor/analysis.py - reading what the learner said.

Two kinds of utterance reach here:

  * one in the target language - measured on the CEFR scale, every mistake
    tied to a skill id from the curriculum, every structure used correctly
    recorded as evidence for that skill;
  * one in the learner's own language - a sign they could not say it in the
    target language. The words they were missing become vocabulary to reuse.

Language detection is local and cheap because it runs on every utterance; the
model gets the final word (it returns is_target_language) before anything is
recorded.
"""
from __future__ import annotations

import json
import re
import sys
import threading
import time
from pathlib import Path

ANALYSIS_MODEL = "gemini-flash-lite-latest"   # per utterance: frequent, cheap
LESSON_MODEL   = "gemini-flash-latest"        # drills and one-off checks


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent




# ── Is this English? ─────────────────────────────────────────────────────────

_AZ_TR_CHARS = set("əğıöüçşİĞÖÜÇŞƏ")

_EN_FUNCTION = {
    "the", "a", "an", "is", "are", "am", "was", "were", "be", "been", "being",
    "i", "you", "he", "she", "it", "we", "they", "me", "my", "your", "his",
    "her", "our", "their", "this", "that", "these", "those", "there",
    "to", "of", "and", "or", "but", "in", "on", "at", "for", "with", "from",
    "about", "into", "over", "after", "before", "because", "if", "when",
    "do", "does", "did", "have", "has", "had", "can", "could", "will",
    "would", "should", "must", "want", "need", "like", "know", "think",
    "what", "how", "why", "where", "who", "not", "no", "yes", "please",
    "let", "get", "go", "make", "take", "give", "tell", "show", "open",
    "close", "play", "find", "help", "very", "some", "any", "all", "more",
}

# Azerbaijani and Turkish words that survive transcription without their
# special letters, which would otherwise read as unknown-but-latin.
_NON_EN_WORDS = {
    "men", "sen", "bir", "ve", "ucun", "bu", "ne", "nece", "salam",
    "yaz", "et", "ac", "var", "yox", "olar", "deyil", "kimi", "ile",
    "ki", "amma", "cox", "yaxsi", "pis", "indi", "sonra",
    "gel", "ol", "ele", "mene", "sene", "bize", "onlar", "hansi",
    "niye", "harada", "zaman", "gun", "saat", "tesekkur", "lutfen",
    "ben", "ama", "icin", "nasil", "evet", "hayir", "tamam", "sey",
}

_WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def words(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


def looks_english(text: str) -> bool:
    toks = words(text)
    if len(toks) < 2:
        return False
    if any(ch in _AZ_TR_CHARS for ch in (text or "").lower()):
        return False
    if any(t in _NON_EN_WORDS for t in toks):
        return False
    hits = sum(1 for t in toks if t in _EN_FUNCTION)
    ratio = hits / len(toks)
    return ratio >= 0.20 or (len(toks) >= 6 and ratio >= 0.15 and hits >= 2)


# ── Did they actually use it? ────────────────────────────────────────────────
# The checklist must tick when the LEARNER says the word, not when the tutor
# does, and it has to survive inflection: "commuting" is "commute", "gave up"
# is "give up", "picked me up" is "pick up". Matching is local and instant -
# asking a model whether a word appeared would cost a round trip per sentence
# and still argue about "gave" versus "give".

_IRREGULAR = {
    "be": ("am", "is", "are", "was", "were", "been", "being"),
    "get": ("got", "gotten"), "go": ("went", "gone", "goes"),
    "wake": ("woke", "woken"), "eat": ("ate", "eaten"), "take": ("took", "taken"),
    "give": ("gave", "given"), "keep": ("kept",), "run": ("ran",),
    "find": ("found",), "grow": ("grew", "grown"), "bring": ("brought",),
    "catch": ("caught",), "think": ("thought",), "stand": ("stood",),
    "come": ("came",), "make": ("made",), "deal": ("dealt",),
    "stick": ("stuck",), "hang": ("hung",), "pay": ("paid",),
    "put": ("put",), "cut": ("cut",), "set": ("set",), "hold": ("held",),
}

# How far after the verb a particle may sit: "pick it up", "put the meeting off".
_PARTICLE_WINDOW = 4


def _token_is(token: str, base: str) -> bool:
    """True if `token` is any ordinary inflection of `base`."""
    if token == base or token in _IRREGULAR.get(base, ()):
        return True
    if len(base) >= 4:
        stem = base[:-1] if base.endswith("e") else base
        if token.startswith(stem) and len(token) - len(stem) <= 4:
            return True
    return False


def used_items(text: str, items: list[str]) -> list[str]:
    """Which of `items` (single words or multi-word phrases) this sentence used."""
    toks = words(text)
    if not toks:
        return []
    found = []
    for item in items:
        parts = [w for w in words(item) if w]
        if not parts:
            continue
        if len(parts) == 1:
            if any(_token_is(t, parts[0]) for t in toks):
                found.append(item)
            continue
        # A phrase: find the head word, then the rest in order close behind it
        # (the object may sit inside a separable phrasal verb).
        head, rest = parts[0], parts[1:]
        heads = [i for i, t in enumerate(toks) if _token_is(t, head)]
        for start in heads:
            at, ok = start, True
            for part in rest:
                window = toks[at + 1: at + 2 + _PARTICLE_WINDOW]
                hit = next((j for j, t in enumerate(window) if _token_is(t, part)), None)
                if hit is None:
                    ok = False
                    break
                at = at + 1 + hit
            if ok:
                found.append(item)
                break
    return found


# ── Talking to the model ─────────────────────────────────────────────────────

# Every model has its own free daily limit. When one is used up (429), or busy
# (503), or gone (404), the next one of the same kind answers instead - and if
# every model of a key is spent, the next key. A spent model rests: a daily
# limit is checked again after an hour, a per-minute one after its delay.
FAST_MODELS = ("gemini-flash-lite-latest", "gemini-3.1-flash-lite", "gemini-3.1-flash-lite-preview",
               "gemini-3.6-flash", "gemini-3-flash-preview")
SMART_MODELS = ("gemini-flash-latest", "gemini-3.6-flash", "gemini-3-flash-preview",
                "gemini-3.1-flash-lite", "gemini-flash-lite-latest")
CALL_TIMEOUT_MS = 30000           # a model that hangs is left for the next one

_clients: dict[str, object] = {}
_client_lock = threading.Lock()
_resting: dict[tuple[str, str], float] = {}     # (key tail, model) -> monotonic time it may be tried again
_last_used: dict[str, str] = {}                 # first model of a chain -> the one that answered


def _keys() -> list[str]:
    try:
        from memory.config_manager import get_gemini_keys
        return get_gemini_keys()
    except Exception:
        return []


def _client_for(key: str):
    with _client_lock:
        if key not in _clients:
            from google import genai
            _clients[key] = genai.Client(api_key=key, http_options={"timeout": CALL_TIMEOUT_MS})
        return _clients[key]


def _chain(model: str) -> list[str]:
    for family in (FAST_MODELS, SMART_MODELS):
        if model in family:
            return [model] + [m for m in family if m != model]
    return [model]


def _rest_for(err: str) -> float | None:
    """How long a model rests after this error, or None if it is not the
    model's fault (a bad prompt) and must be raised."""
    if "429" in err or "RESOURCE_EXHAUSTED" in err:
        if "PerDay" in err:
            return 3600.0
        m = re.search(r"retry in ([\d.]+)s", err)
        return float(m.group(1)) + 1 if m else 60.0
    if "404" in err or "NOT_FOUND" in err:
        return 24 * 3600.0
    if any(k in err for k in ("503", "UNAVAILABLE", "500", "INTERNAL", "timed out", "Timeout", "DEADLINE")):
        return 60.0
    return None


def gemini(prompt: str, model: str = ANALYSIS_MODEL, audio_wav: bytes | None = None,
           json_out: bool = False) -> str:
    contents: object = prompt
    if audio_wav:
        from google.genai import types
        contents = [types.Part.from_bytes(data=audio_wav, mime_type="audio/wav"), prompt]
    config = {"response_mime_type": "application/json"} if json_out else None
    last: Exception | None = None
    keys = _keys()
    if not keys:
        raise RuntimeError("No Gemini API key - add one in Settings.")
    for n, key in enumerate(keys):
        tail = key[-6:]
        for m in _chain(model):
            if time.monotonic() < _resting.get((tail, m), 0.0):
                continue
            try:
                resp = _client_for(key).models.generate_content(model=m, contents=contents, config=config)
            except Exception as e:
                err = str(e)
                if "API key not valid" in err or "API_KEY_INVALID" in err or "PERMISSION_DENIED" in err:
                    last = e
                    break                       # this key is no good: the next key
                rest = _rest_for(err)
                if rest is None:
                    raise
                _resting[(tail, m)] = time.monotonic() + rest
                print(f"[Analysis] {m}{' (key ' + str(n + 1) + ')' if n else ''} not available "
                      f"({err[:40]}) - trying the next model")
                last = e
                continue
            used = f"{m}{' · key ' + str(n + 1) if n else ''}"
            if _last_used.get(model) != used:
                if model in _last_used or used != model:
                    print(f"[Analysis] now using {used}")
                _last_used[model] = used
            return (getattr(resp, "text", "") or "").strip()
    raise last or RuntimeError("Every Gemini model is resting - try again later.")


def parse_json(raw: str) -> dict:
    """Tolerant: models wrap JSON in fences or add a sentence before it."""
    text = (raw or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(text[start:end + 1])
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


# ── Scoring rules ────────────────────────────────────────────────────────────

# You cannot demonstrate B2 in four words. A short utterance with nothing wrong
# in it is an absence of evidence, so the score it can contribute is capped by
# how much language it actually contained.
_LENGTH_CEILINGS = ((4, 40.0), (7, 55.0), (12, 70.0), (19, 85.0))


def length_ceiling(word_count: int) -> float:
    for limit, ceiling in _LENGTH_CEILINGS:
        if word_count <= limit:
            return ceiling
    return 100.0


_STRICTNESS_RULES = {
    "gentle": ("Report only mistakes a listener would notice or that change the "
               "meaning. Let small slips go."),
    "normal": ("Report real grammar and word-choice mistakes. Ignore hesitations "
               "and self-corrections."),
    "strict": ("Report every grammar, word-choice and word-order mistake, "
               "including small ones."),
}


# ── The board: an explanation written for THIS mistake ──────────────────────
# The analyser (and make_board, for a click or an "explain" request) writes the
# whiteboard itself - the rule as it applies to what the learner said, their
# own sentence as the example, and the picture that shows it best. The fixed
# cards in curriculum.py are only the fallback when the model gives nothing.

BOARD_RULES = """- "board": the whiteboard explanation, written for THIS learner and THIS
  mistake - never a generic textbook page. Explain the FIRST correction (or,
  when "request" is "explain", what they asked about). Every word of it
  (title, rule, formula, labels, examples) in very simple {explain_in} at
  their level.
  {"title": "what went wrong, max 6 words, e.g. 'share WITH someone'",
   "rule": "one or two short sentences: why THEIR words were wrong and what to do",
   "formula": ["1 or 2 short patterns, max 45 characters each"],
   "diagram": ONE picture that makes THIS point clear - choose the kind that fits:
     {"kind": "fix", "wrong": ["their", "sentence", "in", "chunks"], "right": ["the", "fixed", "chunks"],
      "bad": [index of the wrong chunk in "wrong"], "good": [index of the fixed chunk in "right"]}
        - their own sentence as blocks, max 7 chunks; best for word choice,
          prepositions, articles, word order and missing words
     {"kind": "timeline", "items": [{"type": "point | range | repeat | cross",
        "at": -1..1, "from": -1..1, "to": -1..1, "label": "max 22 characters"}]}
        - for tenses: WHEN it happens (-1 past, 0 now, 1 future), max 3 items
     {"kind": "split", "left": {"title": "max 18 chars", "lines": ["max 3 lines, 24 chars"]},
      "right": {"title": "...", "lines": ["..."]}}
        - two forms side by side (their wrong use vs the right one, or two rules)
     {"kind": "flow", "items": ["chunk", "→", "chunk", "→", "chunk"]}
        - how the sentence is built, step by step, max 6 items
     {"kind": "ladder", "items": ["big", "bigger", "the biggest"]} - forms that grow
   "examples": ["2 short example sentences about the learner's own life or the topic"]}
  Give {} when there is no correction and no explain request."""

_DIAGRAM_KINDS = ("fix", "timeline", "split", "flow", "ladder", "blocks", "nest", "shift")


def _short(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


def _clean_diagram(d) -> dict | None:
    """Only a picture the board can draw: known kind, short labels, sane numbers."""
    if not isinstance(d, dict) or d.get("kind") not in _DIAGRAM_KINDS:
        return None
    kind = d["kind"]
    num = lambda v: max(-0.9, min(0.9, float(v)))     # the ends of the line stay on the board
    try:
        if kind == "fix":
            wrong = [_short(x, 24) for x in (d.get("wrong") or []) if _short(x, 24)][:8]
            right = [_short(x, 24) for x in (d.get("right") or []) if _short(x, 24)][:8]
            bad = [int(i) for i in (d.get("bad") or []) if 0 <= int(i) < len(wrong)]
            good = [int(i) for i in (d.get("good") or []) if 0 <= int(i) < len(right)]
            if not wrong or not right:
                return None
            return {"kind": kind, "wrong": wrong, "right": right, "bad": bad, "good": good}
        if kind == "timeline":
            items = []
            for it in (d.get("items") or [])[:4]:
                if not isinstance(it, dict) or it.get("type") not in ("point", "range", "repeat", "cross", "arrow"):
                    continue
                row = {"type": it["type"], "label": _short(it.get("label"), 24)}
                if it["type"] in ("point", "cross"):
                    row["at"] = num(it.get("at", 0))
                else:
                    row["from"], row["to"] = sorted((num(it.get("from", -0.5)), num(it.get("to", 0))))
                items.append(row)
            return {"kind": kind, "items": items} if items else None
        if kind == "split":
            cols = []
            for side in ("left", "right"):
                c = d.get(side) if isinstance(d.get(side), dict) else {}
                cols.append({"title": _short(c.get("title"), 20),
                             "lines": [_short(x, 28) for x in (c.get("lines") or []) if _short(x, 28)][:3]})
            if not (cols[0]["lines"] or cols[1]["lines"]):
                return None
            return {"kind": kind, "left": cols[0], "right": cols[1]}
        if kind in ("flow", "ladder", "blocks"):
            items = [_short(x, 22) for x in (d.get("items") or []) if _short(x, 22)][:7]
            return {"kind": kind, "items": items} if len(items) >= 2 else None
        if kind in ("nest", "shift"):
            items = [[_short(a, 22), _short(b, 26)] for a, b in
                     (x for x in (d.get("items") or []) if isinstance(x, (list, tuple)) and len(x) == 2)][:4]
            return {"kind": kind, "items": items} if items else None
    except (TypeError, ValueError):
        return None
    return None


def clean_board(board) -> dict | None:
    """The model's board, checked - or None, and the fixed card is used."""
    if not isinstance(board, dict):
        return None
    rule = _short(board.get("rule"), 220)
    title = _short(board.get("title"), 60)
    if not rule or not title:
        return None
    return {"title": title, "rule": rule,
            "formula": [_short(f, 60) for f in (board.get("formula") or []) if _short(f, 60)][:2],
            "diagram": _clean_diagram(board.get("diagram")),
            "examples": [_short(e, 110) for e in (board.get("examples") or []) if _short(e, 110)][:2]}


def make_board(*, language_name: str, level: str, skill_name: str, hint: str = "",
               said: str = "", wrong: str = "", right: str = "", topic: str = "",
               facts: str = "", explain_in: str = "English") -> dict | None:
    """The board for a correction the learner clicked, or a rule they asked
    about - one quick call."""
    if wrong or right:
        what = (f'The learner said: "{said}". The mistake: "{wrong}" -> "{right}" '
                f"({skill_name}: {hint}). Explain THIS mistake.")
    else:
        what = (f'The learner asked about the rule "{skill_name}" ({hint}). Explain it for them'
                + (f' - their last sentence was "{said}".' if said else "."))
    prompt = f"""You are a {language_name} teacher at a whiteboard, teaching a {level} learner.
{what}
Topic of the conversation: {topic or "anything"}. What we know about them: {facts or "nothing yet"}.

Return ONLY JSON: {{"board": {{...}}}} with
{BOARD_RULES.replace("{explain_in}", explain_in)}"""
    try:
        return clean_board(parse_json(gemini(prompt, json_out=True)).get("board"))
    except Exception as e:
        print(f"[Analysis] board: {e}")
        return None


def _upgrade_hint(language_name: str) -> str:
    if language_name == "English":
        return ('FIRST choice a phrasal verb ("work on" -> "get on with", "finish" -> "wrap '
                'up", "learn" -> "pick up", "understand" -> "figure out"), then a collocation '
                '("do a project" -> "take on a project"), then a stronger word or a ready expression.')
    return (f"FIRST choice a fixed phrase or collocation a native {language_name} speaker "
            "uses, then a more precise verb, then a stronger word or a ready spoken expression.")


def _skill_catalogue(skills: dict) -> str:
    # The hint says what a skill is FOR - "prepositions" alone would take
    # every preposition mistake, "share for you" included.
    return "\n".join(f"  {sid}: {name} ({band}) - {hint}"
                     for sid, (name, band, hint) in skills.items())


def _next_band(level: str) -> str:
    order = ("A1", "A2", "B1", "B2", "C1", "C2")
    i = order.index(level) if level in order else 1
    return order[min(i + 1, len(order) - 1)]


def analysis_prompt(text: str, *, language_name: str, native_language: str,
                    level: str, unit_title: str, unit_skills: list[str],
                    skills: dict, strictness: str,
                    live_dictionary: list | None = None,
                    topic_name: str = "", known_words: list | None = None,
                    scenario: str = "", question: str = "", explain_in: str = "English",
                    from_audio: bool = False) -> str:
    targets = ", ".join(unit_skills) or "none"
    if from_audio:
        utterance = (
            "THE UTTERANCE is the attached audio of the learner speaking.\n"
            "FIRST write it down in \"transcript\" EXACTLY as spoken - every word, "
            "every grammar mistake kept as it was said (\"I go yesterday\" stays \"I go "
            "yesterday\"), nothing added, nothing corrected, names of places and people "
            "exactly as heard - with normal capital letters and punctuation. Then analyse "
            "THAT transcript.")
        transcript_field = '\n  "transcript": "exactly what they said, mistakes kept",'
    else:
        utterance = f'THE UTTERANCE (automatic speech-to-text transcript):\n"""{text}"""'
        transcript_field = ""
    up = _next_band(level)
    lexis = ""
    if live_dictionary:
        lexis += ("\nTHE TOPIC'S WORD LIST (prefer these in \"improved\" when one fits): "
                  + ", ".join(live_dictionary) + "\n")
    if known_words:
        lexis += ("Items the learner has ALREADY learned (reuse one in \"improved\" "
                  "only when it fits THIS topic and THIS sentence): " + ", ".join(known_words[:30]) + "\n")
    topic_line = f'The conversation topic is "{topic_name}".\n' if topic_name else ""
    if scenario:
        topic_line += f'The learner\'s scenario for this topic: """{scenario[:1200]}"""\n'
    if question:
        topic_line += f'The tutor has just said / asked: "{question[-300:]}"\n'
    return f"""You are a {language_name} teacher analysing ONE sentence spoken aloud by
a learner. Their native language is {native_language}. Their level is about {level}.
{topic_line}The grammar being learned now is "{unit_title}", practising: {targets}.{lexis}

{utterance}

HOW TO READ IT:
- It is a transcript. Ignore punctuation, capitalisation, "um", repeated words
  and obvious speech-to-text errors on names.
- Judge grammar, word choice, word order and naturalness.
- {_STRICTNESS_RULES.get(strictness, _STRICTNESS_RULES['normal'])}
- Never invent a mistake. Correct language gets an empty corrections list.
- A sentence that is correct in a normal situation is NOT a mistake: never
  change its tense, its words or its style just because you would say it
  differently ("I grab a bite" is correct - do not turn it into "I'm grabbing").

SKILL IDS (use ONLY these ids in "skill" and "correct_uses"):
{_skill_catalogue(skills)}

Return ONLY a JSON object:
{{{transcript_field}
  "is_target_language": true,
  "score": 0-100,
  "corrections": [
    {{"wrong": "exact phrase they said", "right": "corrected phrase",
      "skill": "skill id", "why": "max 10 simple words"}}
  ],
  "correct_uses": ["skill ids this sentence used CORRECTLY"],
  "corrected": "their whole sentence, fixed, keeping their own words and meaning",
  "improved": "the CORRECTED sentence said better at {up} level - usually with a phrasal verb or collocation",
  "enrich": [
    {{"from": "the plain words in the corrected sentence", "to": "what replaced them in improved",
      "type": "phrasal | collocation | word | expression",
      "level": "{up}", "meaning": "very simple {explain_in}, max 8 words",
      "native": "{native_language} translation of the new item",
      "why": "why it is better, max 12 simple words"}}
  ],
  "misused": ["items from the word lists above that the learner used with a WRONG meaning or in a wrong way"],
  "board": {{"title": "...", "rule": "...", "formula": ["..."], "diagram": {{"kind": "..."}}, "examples": ["..."]}},
  "request": {{"kind": "none | explain | skip | ask", "about": "the grammar point or word they want explained, in English"}},
  "vocab": ["every content word, phrasal verb and fixed chunk the learner USED in this sentence, in its base form, spelled correctly: 'went' -> 'go', 'cutting down on' -> 'cut down on'"],
  "praise": "if the sentence was already correct: three words on what was good, otherwise empty",
  "native_words": [{{"native": "word in {native_language}", "target": "{language_name} word"}}]
}}

RULES:
- "score": how good THIS sentence is on the CEFR scale
  (A1 under 20, A2 20-37, B1 38-55, B2 56-73, C1 74-88, C2 89+).
- "corrections": at most 3, most important first.
- "correct_uses": only structures clearly present AND correct. A sentence in
  the past with a right past verb counts for past_simple; "I like it" does not
  count for anything advanced. Pay special attention to the lesson targets.
- "native_words": {native_language} words mixed into the sentence, with the
  {language_name} word they needed. Empty if none.
- "improved" and "enrich": the learner wants EVERY sentence lifted one level,
  so give them almost always. Build "improved" from the CORRECTED sentence:
  keep its words and change ONLY the parts listed in "enrich". Swap one or two
  plain parts for what a fluent speaker would say - {_upgrade_hint(language_name)} "from" is
  the plain part of the corrected sentence; "to" replaces it, is always
  different and appears word for word in "improved". 1 or 2 items, one level
  above {level} ({up}), never two. Prefer the topic's word list when one fits.
  The new item must MEAN the same as what it replaces in this sentence
  ("learn" is "pick up", never "catch up on"; "work on a project" can be
  "get on with a project").
- NEVER change a fact: the person's job, name, place, time, people and what
  happened stay exactly as they said ("programmer" stays "programmer",
  "yesterday" stays "yesterday"). Upgrade only HOW it is said.
- Do not invent new content: no reason, activity or detail they did not say
  ("... because I am busy today" is nonsense). The sentence may get a little
  longer only through the upgrade itself.
- Only for a greeting, a name, a yes / no, or an answer of three words or
  fewer give "improved": "" and "enrich": [].
- "misused": only items from the lists above, only when clearly wrong. Usually empty.
{BOARD_RULES.replace("{explain_in}", explain_in)}
- "request": "explain" when the learner is asking the TEACHER to explain or
  teach something ("explain present tense", "can you explain the past
  simple?", "what is a phrasal verb?"); "skip" when they ask to skip or move
  on; "ask" when they talk TO the tutor instead of practising: they ask why it
  corrected them or showed something ("why do you show me in on at?"), say it
  is wrong, ask a real question that needs a real answer, or tell it how to
  work ("speak slower", "don't correct small things", "let's just chat");
  otherwise "none". A request is still checked for mistakes.
- "skill": pick the skill whose description fits the mistake itself. A
  preposition that belongs to a verb or adjective ("share with", "listen to",
  "good at") is dependent_prepositions, not prepositions (in / on / at for
  time and place).
- "is_target_language": false if the sentence is not mainly {language_name}.
"""


def pcm_to_wav(pcm16k: bytes) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(pcm16k)
    return buf.getvalue()


def analyse_audio(pcm16k: bytes, **ctx) -> tuple[str, dict]:
    """Hear the learner's own voice, write down exactly what they said - their
    mistakes kept, which live speech-to-text tends to smooth over - and analyse
    it, in ONE call. Returns (transcript, analysis); the analysis is {} when the
    speech was not in the target language or was unusable."""
    raw = gemini(analysis_prompt("", from_audio=True, **ctx), audio_wav=pcm_to_wav(pcm16k))
    data = parse_json(raw)
    text = str(data.get("transcript") or "").strip()
    if not text:
        return "", {}
    return text, _finish(data, text, ctx["skills"])


def transcribe(pcm16k: bytes, language_name: str = "English", expected: str = "",
               vocabulary: list[str] | None = None, native_language: str = "") -> str:
    """Only the words - for a repeat, where there is nothing new to analyse.

    A beginner's accent is hard to hear, so for a repeat the transcriber may be
    given the lesson's words - for spelling only. It is never told the sentence
    the learner was asked to say: told that, it writes the expected sentence
    instead of what was said ("Bývam v Prešove" came out as "Bývam v
    Bratislave"), and every answer looks right. `expected` is kept for old
    callers and ignored. A language other than English goes to the stronger
    model: the light one hears beginner Slovak badly."""
    hints = []
    if vocabulary:
        hints.append("Words from their lesson, ONLY to help with spelling (never write one "
                     "that was not clearly spoken): " + ", ".join(vocabulary[:40]) + ".")
    prompt = (
        f"Transcribe this audio. The speaker is a beginner learner of {language_name}"
        + (f" (native language {native_language})" if native_language else "")
        + ", with an accent and slow, careful speech. " + " ".join(hints)
        + f" Write exactly what they really said, word for word. Spell {language_name} words "
        f"correctly, with all diacritics. Names of places and people exactly as heard. Keep "
        "their grammar mistakes and missing words, never correct or complete the sentence. "
        "If they speak another language, write that as said. Return only the words.")
    model = ANALYSIS_MODEL if language_name == "English" else LESSON_MODEL
    return gemini(prompt, model=model, audio_wav=pcm_to_wav(pcm16k)).strip().strip('"')


def analyse(text: str, **ctx) -> dict:
    """Analyse one target-language utterance. {} when unusable."""
    return _finish(parse_json(gemini(analysis_prompt(text, **ctx))), text, ctx["skills"])


def _finish(data: dict, text: str, skills: dict) -> dict:
    if not data or not data.get("is_target_language", True):
        return {}
    try:
        score = float(data.get("score", 0))
    except Exception:
        score = 0.0
    score = max(0.0, min(100.0, score))
    data["raw_score"] = score
    data["score"] = min(score, length_ceiling(len(words(text))))

    corrections = []
    for c in data.get("corrections") or []:
        if not isinstance(c, dict) or not c.get("right"):
            continue
        sid = str(c.get("skill", "")).strip()
        c["skill"] = sid if sid in skills else "word_choice"
        corrections.append(c)
    data["corrections"] = corrections[:3]

    wrong_skills = {c["skill"] for c in data["corrections"]}
    data["correct_uses"] = [s for s in dict.fromkeys(data.get("correct_uses") or [])
                            if s in skills and s not in wrong_skills][:5]
    data["native_words"] = [w for w in (data.get("native_words") or [])
                            if isinstance(w, dict) and w.get("target")][:5]
    for key in ("corrected", "improved", "praise"):
        data[key] = str(data.get(key) or "").strip()
    if not data["corrected"]:
        data["corrected"] = text.strip()

    enrich = []
    improved_low = data["improved"].lower()
    for e in data.get("enrich") or []:
        if not isinstance(e, dict):
            continue
        to = str(e.get("to") or "").strip()
        if not to or to.lower() not in improved_low:
            continue            # it must be findable on the board
        if to.lower() == str(e.get("from") or "").strip().lower():
            continue            # "find out instead of find out" teaches nothing
        kind = str(e.get("type") or "word").strip().lower()
        enrich.append({
            "from": str(e.get("from") or "").strip()[:60], "to": to[:60],
            "type": kind if kind in ("phrasal", "collocation", "word", "expression") else "word",
            "level": str(e.get("level") or "").strip().upper()[:2],
            "meaning": str(e.get("meaning") or "").strip()[:80],
            "native": str(e.get("native") or "").strip()[:60],
            "why": str(e.get("why") or "").strip()[:100],
        })
    data["enrich"] = enrich[:3]
    if not data["enrich"]:
        # A "better" version with nothing new in it to explain teaches nothing.
        data["improved"] = ""
    data["improved_uses"] = [e["to"] for e in data["enrich"]]
    data["board"] = clean_board(data.get("board"))
    data["misused"] = [str(x).strip().lower() for x in (data.get("misused") or [])
                       if str(x).strip()][:5]
    data["vocab"] = [str(x).strip().lower() for x in (data.get("vocab") or [])
                     if str(x).strip()][:20]
    req = data.get("request") if isinstance(data.get("request"), dict) else {}
    kind = str(req.get("kind") or "none").strip().lower()
    data["request"] = {"kind": kind if kind in ("explain", "skip", "ask") else "none",
                       "about": str(req.get("about") or "").strip()[:60]}
    return data


# ── The correction, word by word ─────────────────────────────────────────────

def diff_tokens(said: str, corrected: str) -> tuple[list[dict], list[dict]]:
    """Two token lists for the correction card: what they said with the wrong
    parts flagged, and the fixed sentence with the repairs flagged.

    Computed locally with difflib rather than asked for: a model marking up its
    own correction drifts between quotation styles and loses words, and the
    learner reads this while the sentence is still in their head.
    """
    import difflib
    a = (said or "").split()
    b = (corrected or "").split()
    left = [{"text": w, "bad": False} for w in a]
    right = [{"text": w, "fixed": False} for w in b]
    if not a or not b:
        return left, right
    strip = " .,!?;:\u201c\u201d\"'"
    matcher = difflib.SequenceMatcher(
        a=[w.lower().strip(strip) for w in a],
        b=[w.lower().strip(strip) for w in b])
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        for i in range(i1, i2):
            left[i]["bad"] = True
        for j in range(j1, j2):
            right[j]["fixed"] = True
    return left, right


def native_help(text: str, *, language_name: str, native_language: str,
                level: str) -> dict:
    """The learner fell back to their own language. Find what they wanted to
    say, at their level, and the words they were missing."""
    prompt = f"""A {level} learner of {language_name} said this in {native_language}
(speech-to-text transcript):
\"\"\"{text}\"\"\"

Return ONLY JSON:
{{
  "is_native": true,
  "target_sentence": "the same meaning in simple {language_name} at {level} level",
  "words": [{{"native": "key {native_language} word", "target": "{language_name} word"}}]
}}
- "words": at most 4 useful content words, not function words.
- "is_native": false if the text is not {native_language} or is only noise.
"""
    data = parse_json(gemini(prompt))
    if not data or not data.get("is_native", True):
        return {}
    data["words"] = [w for w in (data.get("words") or [])
                     if isinstance(w, dict) and w.get("target")][:4]
    return data


def drill(*, language_name: str, native_language: str, level: str,
          skill_name: str, hint: str, mistakes: list[str],
          technique: str = "") -> str:
    """One spoken exercise, built as a named teaching technique.

    Without `technique` a model writes a quiz - five unrelated gap-fills. Given
    the steps of a substitution drill, a dictogloss or a 4/3/2, it writes that
    instead, which is what the unit is supposed to be practised with.
    """
    examples = ("Mistakes this learner really made:\n" + "\n".join(mistakes[:5])
                if mistakes else "No stored mistakes for this skill yet.")
    method = (f"\nRUN IT AS THIS TECHNIQUE - the prompts must fit it:\n{technique}\n"
              if technique else "")
    prompt = f"""Write a short SPOKEN {language_name} drill for a {level} learner
(native language: {native_language}) on "{skill_name}" ({hint}).
{method}
{examples}

Give exactly, as plain sentences with no markdown:
1. The rule in one simple sentence (max 15 words).
2. One example sentence.
3. Five short prompts the learner answers OUT LOUD, from easy to harder, in the
   shape the technique above calls for. Build some from the real mistakes.
4. The answers, after the prompts.
Under 150 words."""
    return gemini(prompt, model=LESSON_MODEL)
