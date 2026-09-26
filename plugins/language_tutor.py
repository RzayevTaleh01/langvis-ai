"""
plugins/language_tutor.py - LangVis as a personal language tutor.

WHAT IT DOES
    LangVis is a speaking teacher, not an assistant. This
    plugin is the teacher's brain, the live voice session is its mouth.

    1. observe(text) - every sentence the learner speaks is analysed in the
       background: scored on the CEFR scale, each mistake tied to a curriculum
       skill, each correct structure counted as evidence. Sentences said in the
       learner's own language are counted too - the words they were missing
       become vocabulary to recycle.
    2. From that evidence the course moves: a unit passes when its grammar
       skills are strong and enough has been said, a stage passes when the level
       is there. The course itself is grammar only.
    2b. Vocabulary is a live dictionary instead of a list: for every sentence
       the analyser proposes words and phrasal verbs from the learner's own
       topic, and each one ticks off after two uses of their own.
    3. format_for_prompt() - every session starts from a LESSON PLAN: the
       current unit, the learner's weakest skills with their real mistakes,
       reviews that are due, words to reuse, and how simply to speak.
    4. Mid-lesson, the tutor is told when something changes: a unit finished,
       the same mistake made three times (→ short focused drill), a correction
       it may have missed.
    5. run() - the learner can ask: my level, my plan, my weak points, check
       this sentence, give me a drill, next unit, pause corrections.

MODES
    English (from A2) and Slovak (from A1, explained in Slovak - the course is
    tutor/slovak.py). See LANGUAGES in tutor/curriculum.py.
"""
from __future__ import annotations

import queue
import re
import threading
import time

from core import store
from tutor import analysis as an
from tutor import curriculum as cur
from tutor import intensive_english, intensive_slovak
from tutor import progress as pg
from tutor import topics as tp


PLUGIN = {
    "name": "language_tutor",
    "description": (
        "The learner's language course. It measures every sentence by itself - "
        "do NOT call it after every sentence. Call it when the learner ASKS: "
        "'what is my level', 'how am I doing' (action='report'); 'what are we "
        "learning', 'what is today's lesson', or after a [TUTOR_PROGRESS] note "
        "if you need the details (action='plan'); 'what are my mistakes', "
        "'what should I study' (action='weak_points'); 'is this sentence "
        "correct' (action='check' with `text`); 'explain the present perfect', 'what "
        "is the passive?' (action='explain' with `topic` - it is drawn on the learner's "
        "board); 'give me exercises', 'test me' "
        "(action='practice', optional `topic`); 'next unit', 'skip this unit' "
        "(action='next_unit'); 'which words should I learn' (action='words'); "
        "'stop correcting me' (action='pause') / 'correct me again' "
        "(action='resume'); 'my level is A2' (action='set_level' with `level`); "
        "'my goal is B2' (action='set_goal' with `level`); 'switch to Slovak' / "
        "'switch to English' (action='set_mode' with `mode`); 'open my "
        "progress file' (action='open_log'); 'let's talk about travel' / "
        "'change the topic to football' (action='set_topic' with `topic`); 'teach me this "
        "topic again', 'give me the words again' (action='teach_again'). In the intensive course: 'next "
        "lesson' (action='next_lesson'), 'repeat this lesson' (action='repeat_lesson')."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": ("report | plan | weak_points | check | practice | "
                                "next_unit | words | pause | resume | set_level | "
                                "set_goal | set_mode | open_log | set_topic | explain | "
                                "teach_again | next_lesson | repeat_lesson. "
                                "Default: report."),
            },
            "text": {"type": "STRING",
                     "description": "For check: the sentence to check."},
            "topic": {"type": "STRING",
                      "description": "For practice: a grammar topic they named "
                                     "(omit to drill their weakest skill). For "
                                     "set_topic: the conversation topic they want, "
                                     "in English, e.g. 'travel' or 'football'."},
            "level": {"type": "STRING",
                      "description": "A CEFR level: A1, A2, B1, B2, C1 or C2."},
            "mode": {"type": "STRING",
                     "description": "For set_mode: english or slovak."},
        },
        "required": [],
    },
}

PLUGIN_SETTINGS = {
    "namespace": "language_tutor",
    "title": "Language tutor",
    "fields": [
        {"key": "mode", "type": "choice", "label": "Language to learn",
         "options": ["English", "Slovak"], "default": "English"},
        {"key": "native_language", "type": "choice", "label": "My own language",
         "options": ["Azerbaijani", "Turkish", "Russian"], "default": "Azerbaijani"},
        {"key": "starting_level", "type": "choice",
         "label": "Start from level (for the language you are learning)",
         "options": ["A1", "A2", "B1", "B2"], "default": "A1"},
        {"key": "goal_level", "type": "choice", "label": "Goal",
         "options": ["B1", "B2", "C1"], "default": "B2"},
        {"key": "pace", "type": "choice", "label": "How fast the tutor speaks",
         "options": ["slow", "normal"], "default": "slow"},
        {"key": "strictness", "type": "choice", "label": "How much to correct",
         "options": ["gentle", "normal", "strict"], "default": "normal"},
        {"key": "speak_every", "type": "choice",
         "label": "Second opinion from the analyser (the tutor already corrects you)",
         "options": ["never (log only)", "3min", "1min", "30s", "always"],
         "default": "never (log only)"},
        {"key": "min_words", "type": "choice", "label": "Ignore sentences shorter than",
         "options": ["2", "3", "4", "5"], "default": "3"},
        {"key": "correct_first", "type": "toggle",
         "label": "Correct my sentence BEFORE answering it",
         "default": True},
    ],
}


# ── Settings ──────────────────────────────────────────────────────────────

_lock = threading.RLock()

# Values the old english_coach stored are honoured until the learner saves
# new ones - except its C1 goal, which was only a default.
_LEGACY_KEYS = {"starting_level", "pace", "strictness"}


def _setting(key: str, fallback):
    try:
        from memory.config_manager import get_plugin_setting
        value = get_plugin_setting("language_tutor", key)
        if value in (None, "") and key in _LEGACY_KEYS:
            value = get_plugin_setting("english_coach", key)
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return fallback


def _mode_key() -> str:
    wanted = str(_setting("mode", "English")).lower().split()[0]
    lang = cur.LANGUAGES.get(wanted)
    return wanted if lang and lang["enabled"] else cur.DEFAULT_LANGUAGE


def _lang() -> dict:
    return cur.language(_mode_key())


def _native() -> str:
    return str(_setting("native_language", "Azerbaijani"))


def _key(lang: dict) -> str:
    """The language's key in the learner's stored data ("english", "slovak")."""
    return lang["data_dir"]


def _load(lang: dict | None = None) -> dict:
    lang = lang or _lang()
    new = not pg.exists(_key(lang))
    state = pg.load(_key(lang))
    if new or not state.get("declared_level"):
        # A language never studied before starts at A1, until the learner
        # picks another starting level in Settings.
        state["declared_level"] = "A1"
    return state


def language_name() -> str:
    """The language being learned - for the session summary and its recap."""
    return _lang()["name"]


def _teach_level(state: dict, lang: dict) -> str:
    """The level the lesson is pitched at: the LOWER of what has been measured
    and the band of the course stage they are in. A few good sentences must not
    lift a beginner out of A1 before the A1 course is done."""
    if _intensive_on():
        return _current_lesson()[1]["band"]
    measured = pg.effective_level(state)[0]
    stages = lang.get("stages") or []
    try:
        stage = stages[int((state.get("course") or {}).get("stage", 0))]
        band = stage.get("band") or measured
    except (IndexError, ValueError, TypeError):
        band = measured
    return band if cur.band_index(band) < cur.band_index(measured) else measured


def _explain_in(level: str | None = None) -> str:
    """The language the rules and corrections are explained in - it can
    depend on the level (Slovak A1 is explained in English)."""
    lang = _lang()
    if level is None:
        try:
            with _lock:
                level = _teach_level(_load(lang), lang)
        except Exception:
            level = ""
    return ((lang.get("explain_by_band") or {}).get(level or "")
            or lang.get("explain_in") or "English")


def _p(key: str, **kw) -> str:
    """A phrase the tutor says around the board, in the language the lesson
    is explained in (a Slovak A1 learner hears "Say it", not "Povedz to")."""
    lang = _lang()
    phrases = lang.get("phrases") or cur.ENGLISH_PHRASES
    if _explain_in() != lang["name"] and _explain_in() == "English":
        phrases = cur.ENGLISH_PHRASES
    text = phrases.get(key) or cur.ENGLISH_PHRASES[key]
    return text.format(**kw) if kw else text


def _save(state: dict, lang: dict | None = None, render: bool = True) -> None:
    lang = lang or _lang()
    pg.save(_key(lang), state)
    if render:
        try:
            pg.render_log(_key(lang), state, lang)
        except Exception as e:
            print(f"[Tutor] log render failed: {e}")


def _min_words() -> int:
    try:
        return max(2, int(str(_setting("min_words", 3))))
    except Exception:
        return 3


_THROTTLE = {"always": 0, "30s": 30, "1min": 60, "3min": 180, "never (log only)": -1}


# ── How the tutor speaks and teaches ─────────────────────────────────────────

_SPEECH_RULES = {
    "A1": "Very short sentences, 6 words or fewer. Present simple only. The most common words.",
    "A2": ("Short sentences, about 8 words, one idea each. Present, past and future "
           "simple only. Everyday words. No idioms. Very few phrasal verbs."),
    "B1": ("Sentences of about 12 words, two clauses at most. Present perfect and "
           "simple conditionals are fine. Common phrasal verbs are fine."),
    "B2": ("Normal sentences up to about 18 words. Any common tense, passive, "
           "relative clauses, ordinary idioms. Avoid rare words."),
    "C1": "Speak naturally with precise vocabulary.",
    "C2": "Speak exactly as to a native speaker.",
}


def _speech_level(state: dict, lang: dict) -> str:
    """How simply the tutor must speak: the LOWER of what has been measured and
    the band of the stage they are working through.

    Measuring one sentence at a time flatters a learner - a good sentence scores
    B1 long before they can hold a B1 conversation. The course knows better: it
    is where their grammar has actually been proved. So the input stays at the
    stage's level and rises as the stage does, which is the point of a course
    that runs from A2 to B2.
    """
    return _teach_level(state, lang)


# ── The topic ────────────────────────────────────────────────────────────────
# What the conversation is about. Chosen by the learner in the header (or by
# asking the tutor); every topic climbs the whole course on its own, and owns a
# fixed word list written once - see tutor/topics.py.

_player = None          # the last player seen, for work that finishes later


def _topic_of(state: dict) -> dict:
    tid = state.get("topic") or tp.DEFAULT_TOPIC
    entry = (state.get("topics") or {}).get(tid) or {}
    topic = tp.find(tid)
    if topic:
        return dict(topic, prompt=entry.get("prompt", ""))
    return {"id": tid, "name": entry.get("name", tid), "az": entry.get("name", tid),
            "subtopics": entry.get("subtopics", []), "custom": True,
            "prompt": entry.get("prompt", "")}


SCENARIO_MAX = 2000      # characters of the learner's own topic instructions


def _scenario_lines(topic: dict) -> list[str]:
    """The learner's own instructions for this topic - a role play, a
    situation, a way of talking. They shape every turn of the conversation."""
    prompt = str(topic.get("prompt") or "").strip()
    if not prompt:
        return []
    return [
        f"THE LEARNER'S SCENARIO FOR THIS TOPIC (follow it for the whole conversation): "
        f"\"{prompt}\"",
        "  If it is a role play, BE that person: talk, ask and answer as them, in their "
        "setting, and keep the learner in their role. Stay in character between the steps - "
        "the corrections, the better versions and the board still happen, then you go "
        "straight back into the scene.",
    ]


def _ensure_topic(state: dict) -> bool:
    """Every learner is in some topic; the first one is Daily life, and it
    inherits the course they already had. Returns True if the state changed."""
    if state.get("topic"):
        return False
    topic = tp.find(tp.DEFAULT_TOPIC)
    return pg.switch_topic(state, topic["id"], topic["name"])


def _lexicon(lang: dict, topic: dict) -> dict | None:
    """The topic's fixed list, or None while it is still being written - in
    which case the writing is started in the background."""
    if not tp.has_lexicon(topic):
        return None
    lex = tp.load_lexicon(_key(lang), topic["id"])
    failed_at, failures = _lexicon_failed.get(topic["id"], (-1e9, 0))
    if (lex is None and not tp.is_building(topic["id"]) and failures < LEXICON_TRIES
            and time.monotonic() - failed_at > LEXICON_RETRY):
        threading.Thread(target=_build_lexicon, args=(lang, topic), daemon=True,
                         name="topic-words").start()
    return lex


LEXICON_RETRY = 45.0                # seconds before a failed word list is tried again
LEXICON_TRIES = 3                   # …and how many times, before giving up until restart
_lexicon_failed: dict[str, tuple[float, int]] = {}


def _build_lexicon(lang: dict, topic: dict) -> None:
    lex = tp.build_lexicon(_key(lang), topic, lang["name"], _native())
    if not lex:
        failures = _lexicon_failed.get(topic["id"], (0.0, 0))[1] + 1
        _lexicon_failed[topic["id"]] = (time.monotonic(), failures)
        _log(_player, f"could not prepare the words for {topic['name']}"
                      + (f" - trying again in {LEXICON_RETRY:.0f} seconds" if failures < LEXICON_TRIES
                         else " - giving up for now; try a clearer topic name"))
        return
    with _lock:
        state = _load(lang)
        pg.sync_topic_deck(state, lex, pg.effective_level(state)[0])
        _save(state, lang, render=False)
        plan = _lesson_plan(state, lang)
    _log(_player, f"the words for {topic['name']} are ready")
    _context(_player, "[TUTOR_PLAN] " + _NOT_THE_LEARNER + " The topic's word list is "
             "ready. Updated plan - use it from now on, do not reply to this:\n\n" + plan)


def _deck(state: dict, lang: dict, lex: dict | None = None) -> dict:
    topic = _topic_of(state)
    if not tp.has_lexicon(topic):
        return pg.suggested_deck(state)
    lex = lex if lex is not None else _lexicon(lang, topic)
    return pg.topic_deck(state, lex, pg.effective_level(state)[0])


def _lesson_plan(state: dict, lang: dict) -> str:
    topic = _topic_of(state)
    level = pg.effective_level(state)[0]
    depth = tp.DEPTH.get(level, tp.DEPTH["B2"] if cur.band_index(level) > 3 else tp.DEPTH["A2"])
    plan = pg.lesson_plan(state, lang, _native(), topic=topic if not topic.get("free") else
                          {"name": "Free talk - anything the learner wants", "subtopics": []},
                          deck=_deck(state, lang), depth=depth)
    scenario = _scenario_lines(topic)
    return plan + ("\n".join(scenario) + "\n" if scenario else "")


_NOT_THE_LEARNER = (
    "This message is from the tutor system, NOT from the learner - they have "
    "said nothing since your last turn. Never answer it as if they had "
    "spoken, never praise a sentence they did not say, never repeat a "
    "question you already asked, and never end the lesson because of it."
)


def _context(player, text: str) -> None:
    """Add something to the tutor's view of the lesson WITHOUT making it speak.
    Falls back to nothing: a silent note must never turn into a spoken turn."""
    fn = getattr(player, "request_context", None)
    if callable(fn):
        try:
            fn(text)
        except Exception as e:
            print(f"[Tutor] context: {e}")


def _method_playbook(lang: dict, state: dict) -> str:
    """The standing techniques, spelled out as instructions.

    A model asked to "teach a lesson" improvises a quiz. These are the ones
    that belong in every conversation whatever the unit is."""
    lines = ["HOW TO TEACH - the method, not just the topic:"]
    for mid in cur.STANDING_METHODS:
        m = cur.method(mid)
        lines.append(f"- {m['name']} - {m['how']}")
    lines += [
        "- Talk time: the learner speaks about 70% of the lesson. If you are "
        "talking more than they are, you are doing it wrong.",
        "- Silence is part of the method: after a question, wait. Do not fill the "
        "gap, do not rephrase immediately, do not answer for them.",
        "",
    ]
    return "\n".join(lines)


def format_for_prompt() -> str:
    """Standing instructions for the live session, rebuilt on every connect."""
    try:
        lang = _lang()
        with _lock:
            state = _load(lang)
            if _ensure_topic(state):
                _save(state, lang, render=False)
        level = _speech_level(state, lang)
        plan = _lesson_plan(state, lang)
        topic = _topic_of(state)
        if _intensive_on():
            idx, lesson = _current_lesson()
            plan = _intensive_plan(idx, lesson, lang)
            topic = {"id": "intensive", "name": f"intensive course, lesson {idx + 1}: {lesson['title']}"}
    except Exception as e:
        print(f"[Tutor] prompt block failed: {e}")
        return ""

    name, native = lang["name"], _native()
    up = cur.BAND_ORDER[min(cur.band_index(level) + 1, len(cur.BAND_ORDER) - 1)]
    slow = str(_setting("pace", "slow")) == "slow"
    other = [l["name"] for k, l in cur.LANGUAGES.items() if k != _mode_key()]
    disabled = [l["name"] for l in cur.LANGUAGES.values() if not l["enabled"]]
    repeat_first = bool(_setting("correct_first", True))

    explain = _explain_in(level)
    # A course is taught strictly, step by step; the Tutor is free conversation.
    strict = _intensive_on()
    if explain != name and explain != native:
        speak_rule = (
            f"You are a personal {name} teacher and nothing else. The learner is a beginner "
            f"in {name}; their native language is {native}. EXPLAIN everything - meanings, "
            f"rules, instructions, corrections - in very simple {explain} (short A2 "
            f"sentences). Everything the learner LEARNS and SAYS - words, phrases, example "
            f"sentences, dialogue lines - is in {name}. Right after every new {name} word "
            f"or sentence, give its {explain} meaning.")
    elif explain == name:
        speak_rule = (
            f"You are a personal {name} speaking teacher and nothing else. The learner's "
            f"native language is {native}. EVERYTHING you say is in {name} - the lesson, "
            f"every explanation, every correction. The learner asked for this. Never use "
            f"{native}" + ("" if name == "English" else " or English") + ". When they do not understand, say it again in even "
            f"simpler {name}: shorter words, an example, a comparison.")
    else:
        speak_rule = (
            f"You are a personal {name} speaking teacher and nothing else. The learner's "
            f"native language is {native}. Speak {name} in the lesson. Use {native} only "
            f"for a one-sentence explanation when they clearly do not understand twice, "
            f"or when they ask what a rule means - then go straight back to {name}.")
    phrases = lang.get("phrases") or cur.ENGLISH_PHRASES
    phrase_rule = None
    if name != "English" and explain == name:
        phrase_rule = (
            "The English words in quotes below are only examples of WHAT to say - in the "
            f"lesson you say them in {name}: Did you mean → \"{phrases['did_you_mean']}\", "
            f"Say it → \"{phrases['say_it']}\", Now you say it → \"{phrases['now_you_say_it']}\", "
            f"Good → \"{phrases['good']}\", Better → \"{phrases['better']}\", "
            f"Again → \"{phrases['again']}\", Look at the board → \"{phrases['look']}\".")
    lines = [
        f"[TUTOR MODE - {name.upper()}]",
        speak_rule,
        phrase_rule,
        "",
        ("YOU ARE THE TEACHER, NOT A CONVERSATION PARTNER. You lead: you GIVE the "
         "learner the words, phrases and model sentences first, and only then ask them "
         "to use them. Never ask them to say something they have not been given the "
         f"{name} for. Every question you ask comes with a model answer or a sentence "
         f"frame they can copy and change (\"{_p('for_example')} ...\")." if strict else
         "YOU ARE A FRIENDLY PERSONAL TUTOR AND A REAL CONVERSATION PARTNER. The learner "
         "leads: talk about anything they want, answer their questions fully, explain any "
         "grammar or word the moment they ask (on the board), play a role if they ask. You "
         "help with gentle guidance - never with drills or repeats they did not ask for."),
        (f"Other language modes: {', '.join(other)}. " if other else "")
        + (f"{', '.join(disabled)} mode is not available yet - if they ask for it, "
           f"say it is coming soon and continue in {name}." if disabled else ""),
        "",
        f"HOW TO SPEAK {name.upper()} (their grammar level is {level}):",
        f"- Your SENTENCES: {_SPEECH_RULES.get(level, _SPEECH_RULES['A2'])}",
        (f"- Your WORDS: only the words taught in this lesson and the most common A1 "
         f"words, each new one with its {explain} meaning right after it."
         if level == "A1" else
         f"- Your WORDS AND PHRASES are one level higher, {up}: collocations, phrasal "
         f"verbs and natural expressions, always inside a clear short sentence, with the "
         f"easy meaning right after a new one: \"I got stuck in traffic - I could not move\"."
         if name == "English" else
         f"- Your WORDS AND PHRASES are one level higher, {up}: fixed phrases and natural "
         f"{name} expressions, always inside a clear short sentence, with the easy meaning "
         f"right after a new one, in simple {name}."),
    ]
    if slow:
        lines.append("- SPEED: speak slowly and clearly, with a real pause at every "
                     "full stop. This never lapses, even in long answers.")
    lines += [
        "- Keep YOUR turns short, then give the floor back. The learner must talk "
        "more than you.",
        "- If they ask you to repeat, say the same thing again, slower and simpler.",
        "",
        (f"THE TOPIC IS \"{topic['name']}\" - the learner chose it on their screen. Stay in "
         "it. " if not topic.get("free") else
         "THIS IS FREE TALK: talk about whatever the learner brings; ask about their life, "
         "work and interests. ")
        + "Grammar has no order here: the learner may ask about ANY rule at any time - "
        "teach it on the board when they do. If they ask to change the topic, call "
        "language_tutor with action='set_topic'.",
        "",
    ]
    if not strict:
        lines += [
            "HOW YOU HELP - guidance, not rules:",
            "- A mistake: say the right version once, in a friendly way (\"We'd say: ...\"), "
            "then answer what they said and carry on. Do NOT make them repeat it, unless they "
            "ask to practise.",
            "- Now and then (not every turn) offer one more natural way to say it, in a few "
            "words: \"You could also say: ...\".",
            "- Keep the talk going: answer, then one follow-up question about what they said.",
            "- They may ask for anything - a grammar rule, a word, how to say something, a role "
            "play, a quick exercise. Do it at once, then go back to talking.",
            "",
        ]
    else:
        lines += [
            "EVERY SENTENCE THE LEARNER SAYS GOES THROUGH THESE THREE STEPS, IN THIS ORDER.",
            "The learner asked for exactly this and does not mind that it is slow:",
        ]
        if repeat_first:
            lines += [
                "  STEP 1 - MISTAKES. If the sentence has a mistake: \"Did you mean: I went "
                "to the office yesterday?\", then explain WHY from the board (the rule is drawn "
                "there) in two or three short sentences, then \"Now say it.\" STOP and wait. "
                "Right → \"Good.\" Still wrong → say it once more, accept it, go on. No "
                "mistake → skip this step with no comment at all.",
            ]
        else:
            lines += [
                "  STEP 1 - MISTAKES. If the sentence has a mistake, say the right version "
                "once (\"You mean: …\") without asking them to repeat it. No mistake → "
                "skip this step with no comment at all.",
            ]
        lines += [
            f"  STEP 2 - SAY IT BETTER, one level up ({up}). Even for a correct sentence. "
            "Give the richer version: \"Better: I was running late because I got stuck "
            "in heavy traffic.\" Explain the new parts in ONE short sentence each, two at "
            "most, with the meaning: \"'got stuck in' - you could not move. 'heavy "
            "traffic' - we say heavy, not big.\" Then: \"Now you say it.\" STOP and wait. "
            "Right → \"Good.\" Still wrong → say it once more, accept it, go on.",
            "  STEP 3 - CONTINUE. Answer what they actually said in one sentence, then ask "
            "the next question in the topic. Build that question so the natural answer "
            "needs ONE item from TOPIC WORDS or OLD WORDS DUE BACK in the plan. If they "
            "then use it right: three words (\"good - 'deal with'\"). If they avoid it: "
            "\"Try it with 'deal with'.\" once, then let it go.",
            "  \"Say it.\" and \"Now you say it.\" END YOUR TURN. They are the last words "
            "you say - nothing after them, not \"Good\", not the next step, not a question. "
            "\"Good\" is only ever said AFTER you have heard the learner say it. Steps 1, 2 "
            "and 3 are three SEPARATE turns of yours, with the learner speaking in between:",
            "    WRONG (one turn): \"You mean: How did you know me? Say it. Good. Better: …\"",
            "    RIGHT: you \"You mean: How did you know me? Say it.\" → learner says it → "
            "you \"Good. Better: How did you recognise me? 'Recognise' - you know someone "
            "again. Now you say it.\" → learner says it → you \"Good. …next question…\"",
            "  Never do step 3 before the repeats. Never answer the content of a sentence "
            "with a mistake before its correction is repeated. Never lose their question: "
            "they must not have to ask twice.",
            "  Skip step 2 for tiny replies (yes / no / one or two words) and for "
            "questions about the lesson itself. Exception to the whole order: when they are "
            "upset or urgent (stop, wait, repeat, I don't understand, help) - answer first.",
            "",
        ]
    lines += [
        "WHAT IS ON THEIR SCREEN - a board, with you standing on it (do not read it out):",
        "- their sentence as they say it, the mistakes in red, the corrected sentence, "
        "the better version with each new item explained and translated, and which "
        "grammar skill went up or down;",
        "- the topic's fixed word list with how often they used each item.",
        "A [BOARD] note tells you exactly what the board shows for their last sentence. "
        "When you reach step 2 and you have it, use EXACTLY its better version, so "
        "your voice and their screen say the same thing. Never reply to a [BOARD] note.",
        "",
        "HOW TO CORRECT, beyond the steps:",
        "- ONE mistake per turn out loud - the most important one, FOCUS list or "
        "current unit first. Smaller ones: use the correct form in your own reply.",
        f"- If they speak {native} because they do not know how to say something: give "
        f"them the simple {name} sentence, ask them to say it, then continue.",
        "- No grammar lectures, no lists, no long praise. Explain a rule in one short "
        "sentence only when they ask or the same mistake keeps coming back.",
        "",
        ("HOW A LESSON RUNS: the course lesson's steps come one by one in [NEXT] notes; "
         "then the speaking task. Your main job is to make them SPEAK as much as possible: "
         "open questions, follow-ups (why? what else? tell me more), and ask them to make a "
         "short answer longer with a linking word. " if strict else
         "HOW IT RUNS: free conversation, led by the learner. Greet them, ask one easy "
         "question in the topic, then follow them. Keep them speaking with real interest in "
         "what they say. ")
        + "Wrap-up only when they want to stop: one thing done well, one to practise, "
        "the new words.",
        "",
        _method_playbook(lang, state),
        "NOTES FROM THE SYSTEM (they arrive as messages; never read a tag aloud):",
        "- [NEXT]: the learner's sentence has ALREADY been checked, and this note says "
        "exactly what your reply is. It overrides everything else here: say what it "
        "says - no more - and when it ends with \"Say it.\" or \"Now you say it.\", "
        "stop there and wait. Never answer the content of a sentence the note says "
        "has a mistake. Never read the note aloud.",
        "- [BOARD]: what the board shows. Silent context - never reply to it.",
        "- [TUTOR_PLAN]: an updated lesson plan. Silent context - never reply to it.",
        "- [TUTOR_NOTE]: a mistake the analyser found. If you already corrected it, "
        "do not repeat it. Otherwise correct it in one short turn.",
        "- [TUTOR_FOCUS]: the same kind of mistake keeps happening. Finish the current "
        "exchange, then run a 2-minute mini-drill on it, then go back to the topic.",
        "- [TUTOR_PROGRESS]: a unit or stage is finished, or the topic changed. Say it "
        "in one sentence and go on with the updated plan.",
        "- [EXPLAIN]: the learner clicked something on the board. Explain it now, "
        "simply, in two or three short sentences, then ask them to use it.",
        "- [FLUENCY]: a fluency round. Ask ONE open question in the topic, then let "
        "them talk for up to two minutes. Do NOT correct and do NOT do the steps "
        "while they talk: only \"mm-hm\", \"go on\", \"and then?\". When they stop or "
        "say they are finished, give the feedback: the two most important mistakes "
        "(say the right versions) and one better phrase - then back to the steps.",
        "- [SKIP]: the learner pressed Skip. Do exactly what the note says.",
        "- [MISHEARD]: the learner says the transcript was wrong. Say sorry in three "
        "words and ask them to say it again. Forget the correction you made.",
        "",
        plan,
    ]
    return "\n".join(l for l in lines if l is not None)


# ── The automatic half ───────────────────────────────────────────────────────

_queue: "queue.Queue" = queue.Queue(maxsize=16)
_worker = None
_worker_lock = threading.Lock()


def observe(text: str, player=None) -> None:
    """Called for EVERY learner utterance. Non-blocking, never raises."""
    try:
        if not text or not text.strip():
            return
        _ensure_worker()
        _queue.put_nowait((text.strip(), player))
    except queue.Full:
        pass
    except Exception as e:
        print(f"[Tutor] observe: {e}")


def _ensure_worker() -> None:
    global _worker
    with _worker_lock:
        if _worker and _worker.is_alive():
            return
        _worker = threading.Thread(target=_worker_loop, name="language-tutor", daemon=True)
        _worker.start()


def _worker_loop() -> None:
    while True:
        text, player = _queue.get()
        try:
            _handle(text, player)
        except Exception as e:
            print(f"[Tutor] {e}")


_last_record: dict = {}     # what "I didn't say that" can take back
_limit_warned = [0.0]       # when the learner was last told the API limit is hit


def _analysis_ctx(state: dict, lang: dict) -> dict:
    """Everything the analyser is told about the learner and the lesson."""
    unit = pg.position(state, lang).get("unit") or {}
    return dict(
        language_name=lang["name"], native_language=_native(),
        level=_teach_level(state, lang),
        unit_title=unit.get("title", "stage review"), unit_skills=unit.get("skills", []),
        skills=lang["skills"], strictness=str(_setting("strictness", "normal")),
        live_dictionary=_hint_words() if _intensive_on() else
        [i["text"] for i in _deck(state, lang).get("items", [])],
        topic_name=_topic_of(state)["name"], scenario=_topic_of(state).get("prompt", ""),
        explain_in=_explain_in(_teach_level(state, lang)),
        question=_turn.get("tutor_last", ""),
        known_words=[k for k, e in state.get("lexis", {}).items() if pg.lexis_stage(e) >= 1])


def _handle(text: str, player, result: dict | None = None, react: bool = True) -> dict:
    """One learner sentence: analyse it (unless `result` already is its
    analysis), record it, put it on the board. With `react` the live tutor is
    told about it afterwards; the thinking gate (below) tells it BEFORE it
    answers instead. Returns what happened, for the gate."""
    global _player
    if player is not None:
        _player = player
    lang = _lang()
    n = len(an.words(text))
    with _lock:
        state = _load(lang)
        if _ensure_topic(state):
            _save(state, lang, render=False)
        paused = bool(state.get("paused"))
        level = pg.effective_level(state)[0]
        topic = _topic_of(state)
        ctx = _analysis_ctx(state, lang)

    is_target = bool(result) or (an.looks_english(text) if _mode_key() == "english" else False)

    if not paused and is_target and _min_words() <= n <= 120:
        if result is None:
            try:
                result = an.analyse(text, **ctx)
            except Exception as e:
                _analysis_failed(player, e)
                return {}
        if result:
            with _lock:
                before_raw = store.get("learner_progress", _key(lang))
                state = _load(lang)
                # The board's upgrades become the learner's too: they were shown
                # and asked to say them, so their uses are counted from now on.
                for e in result.get("enrich", []):
                    pg.add_lexis(state, {"text": e["to"], "kind": e["type"],
                                         "level": e["level"], "meaning": e["meaning"],
                                         "native": e["native"]},
                                 topic=topic["id"], source="board")
                lex = tp.load_lexicon(_key(lang), topic["id"])
                pg.sync_topic_all(state, lex)
                pg.sync_topic_deck(state, lex, level)
                # Their own words are their vocabulary: into the dictionary,
                # counted like any other use.
                pg.record_vocab(state, result.get("vocab", []), topic=topic["id"])
                # What they used is decided locally, never by the model:
                # matching handles inflection and cannot invent a tick.
                used = an.used_items(text, pg.known_items(state))
                outcome = pg.record_target(state, lang, text, result, n,
                                           used_lexis=used)
                _save(state, lang)
                _last_record.clear()
                _last_record.update(raw=before_raw, text=text,
                                    count=state["totals"].get("target_utterances", 0))
            card = build_card(text, result, lang, level)
            card["skill_changes"] = outcome.get("skill_changes", [])
            card["used"] = used
            card["learned"] = outcome.get("checked", [])
            _set_coaching(card)
            _log(player, f"{lang['name']}: {band_label(result['score'])}, "
                         f"{len(result['corrections'])} fix(es), "
                         f"{len(result['correct_uses'])} correct use(s)"
                         + (f", used {', '.join(used)}" if used else ""))
            for item in outcome.get("checked", []):
                _log(player, f"learned: {item}")
            if react:
                _react(player, lang, text, result, outcome)
            return {"kind": "target", "result": result, "outcome": outcome, "used": used}

    if not is_target and n >= 2:
        try:
            help_data = an.native_help(text, language_name=lang["name"],
                                       native_language=_native(), level=level)
        except Exception as e:
            _analysis_failed(player, e)
            return {}
        if help_data:
            with _lock:
                state = _load(lang)
                pg.record_native(state, help_data)
                _save(state, lang)
            _log(player, f"own language → {help_data.get('target_sentence', '')[:60]}")
            return {"kind": "native", "help": help_data}

    with _lock:
        state = _load(lang)
        pg.record_heard(state)
        _save(state, lang, render=False)
    return {}


# ── Thinking before answering (web) ──────────────────────────────────────────
# A live voice model answers the instant the learner stops - before anything
# has looked at what they said - so it answers sentences it should have
# corrected, and it cannot tell a real repeat from a new sentence. In the web
# version the server holds the tutor's turn until the sentence is analysed, and
# this state machine decides the tutor's next move. The tutor is handed that
# move as a [NEXT] note and only has to say it:
#
#   free          their own sentence → mistake?  "Did you mean …? Say it."  → repeat_fix
#                                      correct?  "Better: … Now you say it." → repeat_better
#   repeat_fix    right (or 2nd try) → "Good. Better: … Now you say it."    → repeat_better
#                 wrong              → "Again: … Say it."
#   repeat_better right (or 2nd try) → "Good." + answer + next topic question → free
#
# A repeat is checked here, by comparing words - it costs no analysis and is
# never counted as a new sentence of theirs.

def _send(player, message: dict) -> None:
    fn = getattr(player or _player, "send", None)
    if callable(fn):
        try:
            fn(message)
        except Exception as e:
            print(f"[Tutor] board: {e}")


def _mode(player, mode: str, expect: str = "") -> None:
    """What the teacher is doing now - the board shows it: correcting, a
    better version, explaining grammar, talking, a fluency round - and what it
    is waiting to hear back, if anything."""
    _send(player, {"type": "mode", "mode": mode, "expect": expect})


def _lesson_card(player, card: dict) -> None:
    """Put a lesson on the board: formula, picture, examples."""
    if card:
        _send(player, {"type": "lesson", "card": card})


def _skill_card(sid: str, mine: list | None = None) -> dict:
    """The board card for one grammar skill, with the learner's own mistakes
    as the first examples - "you said this, say it like this"."""
    lang = _lang()
    if sid not in lang["skills"]:
        return {}
    card = cur.board_card(sid, lang["skills"])
    if mine is None:
        with _lock:
            sk = _load(lang).get("skills", {}).get(sid, {})
        mine = [{"wrong": e["wrong"], "right": e["right"]} for e in sk.get("examples", [])[-2:]]
    card["mine"] = mine
    return card


def _ai_card(card: dict, board: dict | None) -> dict:
    """The fixed card for a skill, with what the model wrote for THIS mistake
    laid over it - the fixed text only fills what the model left out."""
    if not board:
        return card
    out = dict(card)
    out["title"] = board.get("title") or card.get("title", "")
    out["rule"] = board.get("rule") or card.get("rule", "")
    out["formula"] = board.get("formula") or card.get("formula", [])
    out["diagram"] = board.get("diagram") or card.get("diagram")
    out["examples"] = board.get("examples") or card.get("examples", [])
    return out


def _board_for(sid: str | None, said: str = "", wrong: str = "", right: str = "") -> dict | None:
    """Ask the model for a board of its own (a click, an "explain" request)."""
    lang = _lang()
    name, _band, hint = lang["skills"].get(sid, (sid or "", "", "")) if sid else ("", "", "")
    if not name:
        return None
    with _lock:
        state = _load(lang)
        level = pg.effective_level(state)[0]
        topic = _topic_of(state)
    return an.make_board(language_name=lang["name"], level=level, skill_name=name, hint=hint,
                         said=said, wrong=wrong, right=right,
                         topic=topic["name"] + (f" - {topic['prompt'][:300]}" if topic.get("prompt") else ""),
                         facts=_memory_facts(300), explain_in=_explain_in(level))


def _picture_words(diagram: dict | None) -> str:
    """What the picture on the board shows, in words the tutor can say while
    it stands next to it."""
    if not diagram:
        return ""
    kind, items = diagram.get("kind"), diagram.get("items") or []
    if kind == "fix":
        wrong, right = diagram.get("wrong") or [], diagram.get("right") or []
        bad = [wrong[i] for i in diagram.get("bad") or [] if i < len(wrong)]
        good = [right[i] for i in diagram.get("good") or [] if i < len(right)]
        if bad and good:
            return _p("fix_picture", bad=" ".join(bad), good=" ".join(good))
        return ""
    if kind == "timeline":
        parts = [it.get("label", "") for it in items if it.get("label")]
        return (_p("timeline") + " " + _p("then").join(parts) + ".") if parts else ""
    if kind == "split":
        left, right = diagram.get("left") or {}, diagram.get("right") or {}
        def lines(col: dict) -> str:
            return ", ".join(str(x).rstrip(".") for x in (col.get("lines") or [])[:2])
        return (f"{_p('left')}, {left.get('title', '')}: {lines(left)}. "
                f"{_p('right')}, {right.get('title', '')}: {lines(right)}.")
    if kind == "flow":
        steps = [str(x) for x in items if str(x) not in ("→", "")]
        return (_p("leads_to").join(steps) + ".") if len(steps) > 1 else ""
    if kind in ("ladder", "blocks"):
        return " - ".join(str(x) for x in items) + "."
    if kind == "nest":
        return " ".join(f"{w.upper()}: {what}." for w, what in items)
    if kind == "shift":
        return " ".join(f"{a} {_p('becomes')} {b}." for a, b in items)
    return ""


def _board_script(card: dict, wrong: str = "", right: str = "", why: str = "") -> str:
    """The explanation the tutor SAYS, in the order the board shows it - rule,
    form, picture, example - so its voice and its walk go together."""
    parts = [_p("look"), card.get("rule", "")]
    formula = card.get("formula") or []
    if formula:
        parts.append(_p("form") + " " + "; ".join(formula[:2]) + ".")
    picture = _picture_words(card.get("diagram"))
    if picture:
        parts.append(picture)
    if wrong and right:
        parts.append(_p("so_not", wrong=wrong, right=right) + (f" {why.rstrip('.')}." if why else ""))
    elif card.get("examples"):
        parts.append(f"{_p('for_example')} {card['examples'][0]}")
    return " ".join(p.strip() for p in parts if p and p.strip())


def _phrase_card(item: dict) -> dict:
    """The board card for a word or phrase: what it replaces, what it means,
    how it is used - in the learner's own sentences first."""
    text = str(item.get("to") or item.get("text") or "").strip()
    if not text:
        return {}
    lang = _lang()
    with _lock:
        entry = _load(lang).get("lexis", {}).get(text.lower(), {})
    plain = str(item.get("from") or "").strip()
    examples = list(entry.get("sentences") or [])[-2:]
    if entry.get("example"):
        examples.append(entry["example"])
    return {"title": text, "band": item.get("level") or entry.get("level", ""),
            "kind": item.get("type") or entry.get("kind", ""),
            "rule": item.get("meaning") or entry.get("meaning", ""),
            "native": item.get("native") or entry.get("native", ""),
            "formula": [f"{plain}  →  {text}"] if plain else [],
            "examples": examples,
            "diagram": {"kind": "flow", "items": [plain, "→", text]} if plain else None,
            "mine": []}


def reset_lesson() -> None:
    """A fresh start: forget the turn in progress and clear the board. The
    chosen topic stays - a reload must not throw the learner out of the topic
    and scenario they picked."""
    _turn.update(phase="free", expected="", better="", enrich=[], said="", attempts=0,
                 events=[], must=[], drill=[], practice=None, last_fix=None, rules=[],
                 tutor_last="", teach=None)
    with _coaching_lock:
        _coaching.clear()
        _coaching["stamp"] = time.time()
        _coaching["reset"] = True


def switch_user() -> None:
    """Another account is signed in (core/profile.py already points at its
    data): nothing of the last learner may reach the new one - not a turn in
    progress, not a sentence still waiting to be analysed, not a cached status."""
    while True:
        try:
            _queue.get_nowait()
        except queue.Empty:
            break
    reset_lesson()
    _last_record.clear()
    _lexicon_failed.clear()
    _starter_failed.clear()
    _status_cache.update(key=None, value={})
    _syllabus_cache.update(key=None, value=[])


REPEAT_OK = 0.75        # share of the words that must match for a good repeat
REPEAT_OTHER = 0.35     # below this it is not a repeat at all but something new
SHORT_TURN = 0.9        # seconds: "yes", "okay" - answered normally, not analysed

_turn: dict = {"phase": "free", "expected": "", "better": "", "enrich": [],
               "said": "", "attempts": 0, "events": [], "must": [], "drill": [],
               "practice": None, "last_fix": None, "rules": [], "tutor_last": "",
               "teach": None}


def _similar(a: str, b: str) -> float:
    import difflib
    wa, wb = an.words(a), an.words(b)
    if not wa or not wb:
        return 0.0
    return difflib.SequenceMatcher(a=wa, b=wb).ratio()


def _explain_items(enrich: list) -> str:
    return " ".join(f"'{e['to']}' - {e['meaning'] or e['why']}." for e in enrich[:2])


def _push_word(state: dict, lang: dict) -> str:
    """One item the next question should make them use: an old one due back
    first, otherwise the topic word they have used least."""
    deck = _deck(state, lang).get("items", [])
    # Old words come back only in free talk: in a topic they would drag the
    # conversation out of it ("project", "schedule" in an introduction).
    if not tp.has_lexicon(_topic_of(state)):
        due = pg.due_lexis(state, limit=1, exclude={i["text"] for i in deck})
        if due:
            return due[0]["text"]
    waiting = sorted((i for i in deck if i["stage"] < 3), key=lambda i: (i["uses"], i["text"]))
    return waiting[0]["text"] if waiting else ""


PRACTICE_QUESTIONS = 3


def _practice_note(said: str, player) -> str | None:
    """While a rule is being practised, the next turn is the next practice
    question instead of the topic."""
    practice = _turn.get("practice")
    if not practice:
        return None
    practice["left"] -= 1
    name = _lang()["skills"].get(practice["skill"], (practice["skill"],))[0]
    if practice["left"] <= 0:
        _turn["practice"] = None
        _mode(player, "talk")
        return (f"The practice of {name} is finished: say so in one short sentence with one "
                "word of praise, then go back to the conversation with ONE easy question. "
                "Then STOP.")
    _mode(player, "explain")
    return (f"Answer what they said in a few words, then ask the next practice question "
            f"for {name} (question {PRACTICE_QUESTIONS - practice['left'] + 1} of "
            f"{PRACTICE_QUESTIONS}) - a new question whose natural answer needs {name}. Then "
            "STOP and wait - never answer it yourself.")


def _step3(said: str, player=None) -> str:
    practice = _practice_note(said, player)
    if practice:
        return practice
    _mode(player, "talk")
    if _turn.get("drill"):
        _lesson_card(player, _skill_card(_turn["drill"][0]))
        _mode(player, "explain")
        _turn["drill"] = []
    lang = _lang()
    with _lock:
        state = _load(lang)
    word = _push_word(state, lang)
    topic = _topic_of(state)
    if _intensive_on():
        idx, lesson = _current_lesson()
        topic, word = {"name": f"{lesson['title']} - {lesson['speak']}", "prompt": ""}, ""
    scenario = topic.get("prompt", "")
    note = (f'Now STEP 3: answer what they originally said ("{said}") in ONE short '
            f'sentence, then ask ONE new question that belongs to the topic "{topic["name"]}"'
            + (" - the next step of the learner's scenario, in your role (it is in your "
               "instructions; follow it)" if scenario else ""))
    note += (f' built so that the natural answer needs "{word}" (do not say the word '
             "yourself - make them use it)" if word else "")
    note += (". After the question give ONE short example answer about THEIR own life, "
             f"from what you remember about them: \"{_p('for_example')} ...\". Then STOP and wait - in silence, as long "
             "as it takes. Never answer your own question, never start an exercise on your "
             "own, never fill the silence.")
    if _turn["events"]:
        note += " Also say in one short sentence: " + " ".join(_turn["events"])
        _turn["events"] = []
    return note


def _better_note(better: str, enrich: list) -> str:
    return (f'say "{_p("better")} {better}" - then explain the new part(s) in one short sentence '
            f"each, in simple {_explain_in()} ({_explain_items(enrich)}) - then say "
            f"\"{_p('now_you_say_it')}\" and STOP.")


def _topic_rule() -> str:
    """Every reply stays in the learner's chosen topic and scenario."""
    if _intensive_on():
        idx, lesson = _current_lesson()
        return (f" This is the intensive course, lesson {idx + 1} (\"{lesson['title']}\"): use only "
                "words the learner has already been taught in the course.")
    try:
        with _lock:
            topic = _topic_of(_load())
    except Exception:
        return ""
    if topic.get("free"):
        return ""
    rule = (f' Stay inside the topic "{topic["name"]}": every question and example '
            "belongs to it - never drift to another subject.")
    if topic.get("prompt"):
        rule += (" Follow the learner's scenario for it exactly (role, steps, rules): "
                 f'"{topic["prompt"][:SCENARIO_MAX]}"')
    return rule


def _next(note: str) -> str:
    rules = _topic_rule()
    if _turn.get("rules"):
        rules += (" The learner's own instructions to you, which win over this note when "
                 "they disagree: " + " | ".join(f'"{r}"' for r in _turn["rules"]) + ".")
    return ("[NEXT] " + _NOT_THE_LEARNER + " What the learner just said has been "
            "checked. Your reply now: " + note + rules
            + " Nothing else, and never read this note aloud.")


# The learner talks TO the tutor - asks why, says it is wrong, tells it how to
# work. That is not a sentence to correct or a rule to draw: it needs a real
# answer, like any assistant would give.
_DIRECT_RE = re.compile(
    r"\bwhy (?:do|did|are|were|does|is) you\b|\bwhy (?:show|showing|this board|that board)\b"
    r"|\bwhy\b.{0,40}\b(?:show(?:ed|ing)?|board|correct(?:ed|ing)?)\b"
    r"|\byou(?:'re| are) wrong\b|\bthat(?:'s| is) (?:wrong|not right|not correct)\b"
    r"|\bwrong (?:board|rule|explanation)\b|\bi (?:didn'?t|did not) (?:ask|mean)\b"
    r"|\bdon'?t correct\b|\bstop (?:correcting|the lesson|teaching|explaining)\b"
    r"|\bspeak (?:more )?(?:slowly|slower|faster)\b"
    r"|\bi have a question for you\b|\bcan i ask you\b"
    r"|\bniy[əe]\b|\bs[əe]hv (?:g[öo]st[əe]r|izah|d[üu]z[əe]lt)",
    re.IGNORECASE)

# The part of it that should last: "from now on …", "don't correct …".
_RULE_RE = re.compile(
    r"\b(?:from now on|always|never|don'?t|do not|stop|please speak|speak (?:more )?(?:slow|fast)|"
    r"just (?:talk|chat))\b", re.IGNORECASE)
MAX_RULES = 4


def _is_direct(text: str) -> bool:
    return bool(_DIRECT_RE.search(text or ""))


def _direct_turn(text: str, player=None) -> str:
    """Answer the learner as a thinking assistant would: what they asked, and
    if the tutor's last correction or board was off, say so and fix it."""
    _turn.update(phase="free", expected="", better="", enrich=[], attempts=0, must=[])
    _turn["practice"] = None
    if _RULE_RE.search(text) and "?" not in text:
        _turn["rules"] = (_turn.get("rules", []) + [text.strip()[:160]])[-MAX_RULES:]
    _mode(player, "talk")
    fix = _turn.get("last_fix") or {}
    context = ""
    if fix:
        context = (f' Your last correction: they said "{fix.get("said", "")}", you changed '
                   f'"{fix.get("wrong", "")}" to "{fix.get("right", "")}"'
                   + (f' ({fix["why"]})' if fix.get("why") else "")
                   + (f' and showed the board "{fix["board"]}"' if fix.get("board") else "") + ".")
    return _next(
        f'the learner is talking to YOU directly: "{text}". This is a question or an '
        "instruction, not practice - do NOT correct it, do NOT improve it and do NOT go "
        "back to the lesson script." + context +
        " Think first, like a smart and honest assistant, then answer exactly what they "
        f"asked in simple {_explain_in()} at their level, in two to four short sentences. If your "
        "correction or your board did not fit their mistake, say so plainly (\"You are "
        "right - that was the wrong rule.\") and give the right, short explanation. If they "
        "told you how to work, say you will do it and do it from now on. Then ask ONE "
        "short question: shall we go on? And STOP.")


def _free_turn(text: str, handled: dict, player=None) -> str | None:
    """Their own new sentence has been analysed and recorded: decide the reply."""
    _turn.update(phase="free", expected="", better="", enrich=[], said=text, attempts=0, must=[])
    if handled.get("kind") == "native":
        target = handled["help"].get("target_sentence", "")
        if not target:
            return None
        _turn.update(phase="repeat_fix", expected=target)
        _mode(player, "correct", target)
        return _next(f'they spoke {_native()}. Say ONLY: "{_p("in_lang")} {target} {_p("say_it")}" and STOP.')
    if handled.get("kind") != "target":
        return None
    result, outcome = handled["result"], handled["outcome"]
    _turn["events"] += outcome.get("events", []) + ([outcome["band_moved"]]
                                                     if outcome.get("band_moved") else [])
    if outcome.get("repeated"):
        names = [_lang()["skills"].get(s, (s,))[0] for s in outcome["repeated"]]
        _turn["events"].append(f"then say in ONE sentence that {', '.join(names)} keeps "
                               "coming back and that its rule and picture are on the board "
                               "now (point at it in one more sentence).")
        _turn["drill"] = list(outcome["repeated"])
    improved = result.get("improved", "")
    if not _intensive_on() and not _turn.get("practice"):
        return _next(_tutor_reply(text, result, player))
    if result["corrections"]:
        c = result["corrections"][0]
        _turn.update(phase="repeat_fix", expected=result["corrected"],
                     better="" if _turn.get("practice") else improved,
                     enrich=result.get("enrich", []),
                     must=[c.get("right", "") for c in result["corrections"] if c.get("right")])
        card = _ai_card(_skill_card(c["skill"], mine=[]), result.get("board"))
        _lesson_card(player, dict(card, mine=[{"wrong": c.get("wrong", ""), "right": c.get("right", "")}]))
        _mode(player, "correct", result["corrected"])
        script = _board_script(card, c.get("wrong", ""), c.get("right", ""), c.get("why", ""))
        _turn["last_fix"] = {"said": text, "wrong": c.get("wrong", ""), "right": c.get("right", ""),
                             "why": c.get("why", ""), "board": card.get("title", "")}
        return _next("their sentence has a mistake. Do NOT answer it or react to its content "
                     "yet. You are a teacher at the board: SAY this, slowly, sentence by "
                     "sentence - every part of it, nothing skipped, your own words are fine "
                     f"but keep the order, and every word in {_explain_in()}: \"{_p('did_you_mean')} "
                     f"{result['corrected']} {script} {_p('now_say_it')} {result['corrected']}\" "
                     "Then STOP and wait.")
    if improved and not _turn.get("practice"):
        _turn.update(phase="repeat_better", expected=improved, enrich=result.get("enrich", []),
                     must=[e["to"] for e in result.get("enrich", [])])
        _mode(player, "better", improved)
        return _next("their sentence is correct - no comment on that. Now " +
                     _better_note(improved, result.get("enrich", [])))
    return _next(_step3(text, player))


def _tutor_reply(text: str, result: dict, player) -> str:
    """The Tutor: guidance, not rules. A mistake is corrected once, kindly, and
    the conversation goes on - nothing has to be repeated. The board still
    shows the correction and the better version."""
    fixes = result.get("corrections") or []
    improved = result.get("improved", "")
    if fixes:
        c = fixes[0]
        _mode(player, "correct", "")
        _turn["last_fix"] = {"said": text, "wrong": c.get("wrong", ""), "right": c.get("right", ""),
                             "why": c.get("why", ""), "board": ""}
        note = (f'their sentence has a small mistake. In a friendly way, say the right version once: '
                f'"We\'d say: {result["corrected"]}"'
                + (f" - with a few words why ({c['why']})" if c.get("why") else "")
                + ". Do NOT ask them to repeat it. Then answer what they said")
    elif improved:
        _mode(player, "better", "")
        note = ("their sentence is correct. Answer what they said, and in passing offer one more "
                f'natural way to say it, in a few words: "You could also say: {improved}". Do NOT '
                "ask them to repeat it. Then carry on")
    else:
        _mode(player, "talk")
        note = "their sentence is correct - no comment on it. Answer what they said"
    return (note + ", and ask ONE follow-up question about it. Keep it natural and short, then "
            "STOP and wait.")


def _missing(text: str) -> list[str]:
    """The parts a repeat must contain - the corrected words, or the new
    phrase - that it does not. Matched like dictionary uses, so "ran late"
    counts for "run late"."""
    must = [m for m in _turn.get("must", []) if m.strip()]
    found = set(an.used_items(text, must)) if must else set()
    return [m for m in must if m not in found and m.lower() not in text.lower()]


def _repeat_ok(text: str) -> bool:
    return _similar(text, _turn["expected"]) >= REPEAT_OK and not _missing(text)


def _repeat_turn(text: str, player=None) -> str | None:
    """They were asked to say something. Was this it - including the part
    that is the whole point of the repeat?"""
    expected = _turn["expected"]
    good = _repeat_ok(text)
    tried = _turn["attempts"] >= 1
    if good or tried:
        prefix = f"say \"{_p('good')}\"" if good else \
            f'say the right version once more ("{expected}"), accept it, then'
        if _turn["phase"] == "repeat_fix" and _turn["better"]:
            _turn.update(phase="repeat_better", expected=_turn["better"], attempts=0,
                         must=[e["to"] for e in _turn["enrich"]])
            _mode(player, "better", _turn["better"])
            return _next(f"{prefix} {_better_note(_turn['better'], _turn['enrich'])}")
        said = _turn["said"]
        _turn.update(phase="free", expected="", better="", enrich=[], attempts=0)
        return _next(f"{prefix} {_step3(said, player)}")
    _turn["attempts"] += 1
    _mode(player, "again", expected)
    missing = _missing(text)
    hint = (f' They left out "{missing[0]}" - that is the part to learn, so say it a little '
            "slower." if missing else "")
    return _next(f'not quite - they said "{text}".{hint} Say ONLY: '
                 f'"{_p("again")} {expected} {_p("say_it")}" and STOP.')


_SKIP_RE = re.compile(r"\b(skip|next|move on|go on|let'?s go on|let'?s continue|pass|"
                      r"ke[çc]|davam)\b", re.IGNORECASE)


_EXPLAIN_RE = re.compile(
    r"\b(explain|teach me|tell me about|what (?:is|are|'s)|what does|how (?:do|can|should) "
    r"(?:i|you|we) use|difference between|help me with|show me|izah|öyrət|oyret|nədir|nedir|"
    r"vysvetli|vysvetlite|nauč ma|čo je|čo znamená|ako sa používa)\b",
    re.IGNORECASE)


def _asked_to_explain(text: str) -> str | None:
    """"Explain relative clauses", "what is the passive", "past simple izah et":
    the skill they want taught, recognised here - never left to the analyser
    alone, so the board always opens."""
    if not _EXPLAIN_RE.search(text or ""):
        return None
    return _find_skill(text, _lang())


def _late() -> bool:
    """The voice session stopped waiting for this sentence: change nothing."""
    return bool(_gate_deadline[0]) and time.monotonic() > _gate_deadline[0]


_gate_deadline = [0.0]


def gate_audio(pcm16k: bytes, seconds: float, player=None, echo=None,
               deadline: float = 0.0) -> dict:
    """The learner has just stopped speaking and the tutor is waiting. Hear
    what they said and decide the reply.

    Returns {"text", "note", "handled"} - or {"drop": True} when nothing was
    actually said (noise, the tutor's own voice): then the model never hears
    it at all. `note` is None when the tutor should simply answer on its own."""
    global _player
    if player is not None:
        _player = player
    _gate_deadline[0] = deadline
    lang = _lang()
    try:
        if seconds < SHORT_TURN or _turn["phase"] != "free":
            text = an.transcribe(pcm16k, lang["name"], vocabulary=_transcribe_hints(),
                                 native_language=_native())
            if not an.words(text):
                return {"drop": True}
            if echo is not None and echo(text):
                print(f"[Tutor] echo dropped: {text[:60]}")
                return {"drop": True}
            if _late():
                return {"text": text, "note": None}
            if _turn["phase"] == "teach":
                _live_sentence(player, text)
                if _SKIP_RE.search(text) and len(an.words(text)) <= 4:
                    return {"text": text, "note": _skip_note(player), "handled": True}
                return {"text": text, "note": _teach_turn(text, player), "handled": True}
            if _is_direct(text):
                _live_sentence(player, text)
                return {"text": text, "note": _direct_turn(text, player), "handled": True}
            if _turn["phase"] != "free":
                sid = _asked_to_explain(text)
                if sid:
                    _live_sentence(player, text)
                    return {"text": text, "note": _explain_turn(text, {}, "", player, sid=sid),
                            "handled": True}
                if _SKIP_RE.search(text) and len(an.words(text)) <= 6:
                    return {"text": text, "note": _skip_note(player), "handled": True}
                if _similar(text, _turn["expected"]) >= REPEAT_OTHER:
                    _repeat_feedback(player, text)
                    return {"text": text, "note": _repeat_turn(text, player), "handled": True}
            if seconds < SHORT_TURN:
                _live_sentence(player, text)
                return {"text": text, "note": None}      # "yes", "okay": answered normally
        with _lock:
            state = _load(lang)
            ctx = _analysis_ctx(state, lang)
            paused = bool(state.get("paused"))
        if paused:
            return {"text": "", "note": None}
        text, result = an.analyse_audio(pcm16k, **ctx)
    except Exception as e:
        _analysis_failed(player, e)
        return {"text": "", "note": None}
    if not an.words(text):
        return {"drop": True}
    if echo is not None and echo(text):
        print(f"[Tutor] echo dropped: {text[:60]}")
        return {"drop": True}
    if _late():
        return {"text": text, "note": None}
    _live_sentence(player, text)
    if _is_direct(text) or ((result or {}).get("request") or {}).get("kind") == "ask":
        return {"text": text, "note": _direct_turn(text, player), "handled": True}
    return _decide(text, result, player)


def gate_text(text: str, player=None) -> dict:
    """The same decision for a typed sentence."""
    global _player
    _gate_deadline[0] = 0.0
    if player is not None:
        _player = player
    text = (text or "").strip()
    if not text:
        return {"text": "", "note": None}
    if _turn["phase"] == "teach":
        _live_sentence(player, text)
        if _SKIP_RE.search(text) and len(an.words(text)) <= 4:
            return {"text": text, "note": _skip_note(player), "handled": True}
        return {"text": text, "note": _teach_turn(text, player), "handled": True}
    if _is_direct(text):
        _live_sentence(player, text)
        return {"text": text, "note": _direct_turn(text, player), "handled": True}
    if _turn["phase"] != "free":
        sid = _asked_to_explain(text)
        if sid:
            _live_sentence(player, text)
            return {"text": text, "note": _explain_turn(text, {}, "", player, sid=sid),
                    "handled": True}
        if _SKIP_RE.search(text) and len(an.words(text)) <= 6:
            return {"text": text, "note": _skip_note(player), "handled": True}
        if _similar(text, _turn["expected"]) >= REPEAT_OTHER:
            _repeat_feedback(player, text)
            return {"text": text, "note": _repeat_turn(text, player), "handled": True}
    _live_sentence(player, text)
    return _decide(text, None, player)


def _decide(text: str, result: dict | None, player) -> dict:
    """Their own new sentence: an instruction to the teacher ("explain the
    past tense") is obeyed; anything else goes through the three steps."""
    sid = _asked_to_explain(text)
    if sid:
        handled = _handle(text, player, result=result or None, react=False) if result else {}
        return {"text": text, "note": _explain_turn(text, handled, "", player, sid=sid),
                "handled": True}
    request = (result or {}).get("request") or {}
    if result is None:
        with _lock:
            ctx = _analysis_ctx(_load(), _lang())
        try:
            result = an.analyse(text, **ctx)
        except Exception as e:
            _analysis_failed(player, e)
            return {"text": text, "note": None}
        request = (result or {}).get("request") or {}
    if request.get("kind") == "ask":
        return {"text": text, "note": _direct_turn(text, player), "handled": True}
    if request.get("kind") == "explain":
        handled = _handle(text, player, result=result or None, react=False)
        return {"text": text, "note": _explain_turn(text, handled, request.get("about", ""), player),
                "handled": True}
    handled = _handle(text, player, result=result or None, react=False)
    return {"text": text, "note": _free_turn(text, handled, player), "handled": True}


def _explain_turn(text: str, handled: dict, about: str, player, sid: str | None = None) -> str:
    """The learner told the teacher what to do. Their sentence is fixed in one
    breath - no repeat, no better version - and the lesson goes on the board."""
    _turn.update(phase="free", expected="", better="", enrich=[], said=text, attempts=0, must=[])
    sid = sid or _find_skill(about or text, _lang())
    card = _skill_card(sid) if sid else {}
    if card:
        board = ((handled or {}).get("result") or {}).get("board") or _board_for(sid, said=text)
        card = _ai_card(card, board)
    if card:
        _lesson_card(player, card)
        _mode(player, "explain")
    else:
        _explain_on_board(about or text, player)
    script = _board_script(card) if card else ""
    if sid:
        _turn["practice"] = {"skill": sid, "left": PRACTICE_QUESTIONS}
    # A request is not practice material: its wording is not corrected.
    return _next("the learner asked you to explain a rule - do NOT correct or improve "
                 "their request, just teach. You are a teacher at the board: SAY this, "
                 "slowly, sentence by sentence - every part of it, nothing skipped: "
                 f"\"{card.get('title', 'This rule')}. {script}\" Then: \"{_p('practise')}\" "
                 "and ask practice question 1 - a question whose natural answer needs this "
                 "rule. Then STOP and wait - never answer it yourself.")


def _skip_note(player) -> str:
    """They want to go on without repeating: fine."""
    if _turn["phase"] == "teach" and _turn.get("teach"):
        return _teach_next("the learner wants to skip this one - fine, no comment.", player)
    said = _turn.get("said", "")
    _turn.update(phase="free", expected="", better="", enrich=[], attempts=0, must=[])
    return _next("the learner wants to skip the repeat - that is fine, no comment. "
                 + _step3(said, player))


def skip_step(player=None) -> tuple[bool, str]:
    """The Skip button: leave the repeat and go on with the conversation."""
    if _turn["phase"] == "free":
        return False, "There is nothing to skip right now."
    _say(player or _player, _skip_note(player).replace("[NEXT]", "[SKIP]", 1), quiet_for=0.2, user_action=True)
    return True, "Skipped - on with the conversation."


# ── The taught part of a topic ───────────────────────────────────────────────
# A topic opens like a real lesson: the teacher gives the words, the word
# partners and the linking words one by one (the learner repeats each), says a
# short model dialogue line by line (the learner says their lines), then gives
# sentence frames the learner finishes about their own life. Only then does the
# free conversation start. The content is written once per topic and level
# (tutor/topics.py - build_starter) and the part is taught once per topic and
# level; "teach me this topic again" runs it again.

STARTER_WAIT = 30.0          # seconds the opening waits for the pack to be written
REPEAT_TEACH = 0.5           # a repeat of a taught word or line: close enough
_starter_failed: dict[str, float] = {}


def _starter_level(state: dict, lang: dict) -> str:
    level = _teach_level(state, lang)
    return level if level in ("A1", "A2", "B1", "B2") else "B2"


def _unit_grammar(state: dict, lang: dict) -> tuple[list[tuple[str, str]], list[str]]:
    """The grammar of the unit they are on - taught inside the topic."""
    unit = pg.position(state, lang).get("unit") or {}
    ids = [sid for sid in unit.get("skills") or [] if sid in lang["skills"]][:2]
    return [(lang["skills"][sid][0], lang["skills"][sid][2]) for sid in ids], ids


def _build_pack(lang: dict, topic: dict, level: str, grammar: list, grammar_ids: list) -> dict | None:
    """The topic's dictionary first (the lesson teaches from it), then the lesson."""
    lex = tp.load_lexicon(_key(lang), topic["id"])
    if lex is None:
        lex = tp.build_lexicon(_key(lang), topic, lang["name"], _native())
    return tp.build_starter(_key(lang), topic, lang["name"], _native(), level, _explain_in(level),
                            lexicon=lex, grammar=grammar, grammar_ids=grammar_ids)


def _starter(state: dict, lang: dict, wait: bool = False) -> dict | None:
    """The topic's taught part, or None (free talk, or still being written -
    then the writing starts in the background; with `wait` it is written now)."""
    topic = _topic_of(state)
    if not tp.has_lexicon(topic):
        return None
    level = _starter_level(state, lang)
    pack = tp.load_starter(_key(lang), topic["id"], level)
    if pack:
        return pack
    key = f"{lang['name']}:{topic['id']}:{level}"
    if time.monotonic() - _starter_failed.get(key, -1e9) < LEXICON_RETRY:
        return None
    grammar, ids = _unit_grammar(state, lang)
    args = (lang, topic, level, grammar, ids)
    if not wait:
        if not tp.is_building(f"starter:{topic['id']}:{level}"):
            threading.Thread(target=_build_pack, args=args, daemon=True,
                             name="topic-starter").start()
        return None
    pack = _build_pack(*args)
    if not pack:
        _starter_failed[key] = time.monotonic()
    return pack


def _taught(state: dict, lang: dict) -> bool:
    entry = (state.get("topics") or {}).get(state.get("topic") or "", {})
    return _starter_level(state, lang) in (entry.get("taught") or [])


def _mark_taught() -> None:
    lang = _lang()
    with _lock:
        state = _load(lang)
        entry = state.setdefault("topics", {}).setdefault(state.get("topic") or "", {})
        level = _starter_level(state, lang)
        entry["taught"] = sorted(set(entry.get("taught") or []) | {level})
        _save(state, lang, render=False)


_SECTION = {
    "review": ("Review", "a quick review of words from earlier lessons"),
    "phrases": ("Phrases", "ready phrases to say"),
    "translate": ("Translate", "translation practice - the learner says it themselves"),
    "build": ("Build sentences", "sentence building - the learner joins or upgrades sentences themselves"),
    "questions": ("Questions for you", "questions about the learner's own life"),
    "words": ("Words", "the key words of the topic"),
    "collocations": ("Word partners", "words that go together"),
    "linkers": ("Linking words", "little words that join sentences"),
    "grammar": ("Grammar", "one grammar point, on this topic"),
    "extend": ("Longer sentences", "how to make a sentence longer"),
    "dialogue": ("Dialogue", "a short dialogue"),
    "frames": ("Your sentences", "your own sentences"),
}


def _teach_steps(pack: dict) -> list[dict]:
    steps: list[dict] = []
    for n, it in enumerate(pack.get("review") or []):
        steps.append({"kind": "review", "first": n == 0, "item": it, "expect": it["text"]})
    for kind in ("words", "collocations", "phrases", "linkers"):
        for n, it in enumerate(pack.get(kind) or []):
            say = it["example"] if kind == "linkers" and it.get("example") else it["text"]
            steps.append({"kind": kind, "first": n == 0, "item": it, "expect": say})
    grammar = pack.get("grammar") or {}
    for n, ex in enumerate(grammar.get("examples") or []):
        steps.append({"kind": "grammar", "first": n == 0, "item": grammar, "expect": ex})
    first = True
    for chain in pack.get("extend") or []:
        for n, part in enumerate(chain):
            steps.append({"kind": "extend", "first": first, "item": part, "chain": chain,
                          "prev": chain[n - 1]["text"] if n else "", "expect": part["text"]})
            first = False
    if pack.get("extend"):
        last = pack["extend"][0][-1]
        steps.append({"kind": "extend", "first": False, "own": True, "chain": pack["extend"][0],
                      "item": last, "expect": last["text"], "open": True})
    partner, first = None, True
    for line in pack.get("dialogue") or []:
        if line["who"] == "partner":
            partner = line
            continue
        steps.append({"kind": "dialogue", "first": first, "partner": partner,
                      "item": line, "expect": line["text"]})
        partner, first = None, False
    for n, tr in enumerate(pack.get("translate") or []):
        steps.append({"kind": "translate", "first": n == 0, "item": tr, "expect": tr["sk"]})
    for n, b in enumerate(pack.get("build") or []):
        steps.append({"kind": "build", "first": n == 0, "item": b, "expect": b["answer"]})
    for n, q in enumerate(pack.get("questions") or []):
        steps.append({"kind": "questions", "first": n == 0, "item": q, "expect": q["example"],
                      "open": True})
    for n, fr in enumerate(pack.get("frames") or []):
        steps.append({"kind": "frames", "first": n == 0, "item": fr,
                      "expect": fr.get("example") or fr["frame"], "open": True})
    return steps


def _teach_card(pack: dict, step: dict) -> dict:
    """The board for this part of the lesson: everything in the section, the
    current item on top with its meaning and example."""
    kind, it = step["kind"], step["item"]
    card = {"title": f"{_SECTION[kind][0]} · {pack.get('name', '')}", "band": pack.get("level", ""),
            "kind": "lesson", "mine": [], "diagram": None, "examples": [], "formula": []}
    if kind == "review":
        card["formula"] = [f"{x['meaning']}  →  ?" for x in pack.get("review") or []]
        card["rule"] = f"{it['meaning']}  →  ?"
        card["native"] = it.get("native", "")
    elif kind == "translate":
        card["formula"] = [t["en"] for t in pack.get("translate") or []]
        card["rule"] = it["en"]
    elif kind == "build":
        card["formula"] = [b["task"] for b in pack.get("build") or []]
        card["rule"] = it["task"]
    elif kind == "questions":
        card["formula"] = [q["q"] for q in pack.get("questions") or []]
        card["rule"] = it["q"]
        card["native"] = it.get("meaning", "")
        card["examples"] = [f"{_p('for_example')} {it['example']}"]
    elif kind in ("words", "collocations", "phrases", "linkers"):
        card["formula"] = [f"{x['text']}  -  {x['meaning']}"
                           + (f"  ({x['native']})" if x.get("native") else "")
                           for x in pack.get(kind) or []]
        card["rule"] = f"{it['text']} - {it['meaning']}"
        card["native"] = it.get("native", "")
        card["examples"] = [it["example"]] if it.get("example") else []
    elif kind == "grammar":
        skills = _lang()["skills"]
        sid = next(iter(it.get("skills") or []), "")
        base = cur.board_card(sid, skills) if sid in skills else {}
        card["title"] = f"{_SECTION[kind][0]} · {it.get('name') or base.get('title', '')}"
        card["kind"] = "grammar"
        card["rule"] = it.get("rule", "")
        card["formula"] = it.get("table") or base.get("formula", [])
        card["diagram"] = base.get("diagram")
        card["examples"] = list(it.get("examples") or [])
    elif kind == "extend":
        card["formula"] = [p["text"] + (f"   + {p['how']}" if p.get("how") else "")
                           for p in step.get("chain") or []]
        card["rule"] = ("Now you: make your own sentence longer" if step.get("own") else
                        (f"+ {it['how']}" if it.get("how") else it["text"]))
    elif kind == "dialogue":
        who = pack.get("partner_role") or "partner"
        card["formula"] = [f"{who if l['who'] == 'partner' else 'You'}: {l['text']}"
                           + (f"  ({l['meaning']})" if l.get("meaning") else "")
                           for l in pack.get("dialogue") or []]
        card["rule"] = f"You: {it['text']}"
        card["native"] = it.get("meaning", "")
    else:
        card["formula"] = [f["frame"] for f in pack.get("frames") or []]
        card["rule"] = it["frame"]
        card["native"] = it.get("meaning", "")
        card["examples"] = (([f"Put in: {it['hint']}"] if it.get("hint") else [])
                            + ([f"{_p('for_example')} {it['example']}"] if it.get("example") else []))
    return card


def _teach_say(pack: dict, step: dict) -> str:
    """What the teacher says for one step - ending with the learner's turn."""
    kind, it = step["kind"], step["item"]
    ex = pack.get("explain_in") or _explain_in()
    say_it = _p("say_it")
    intro = ""
    if step["first"]:
        what = _SECTION[kind][1]
        if kind == "dialogue":
            intro = (f"(In {ex}: now {what} - you are the {pack.get('partner_role') or 'partner'}, "
                     "the learner says their own lines.) ")
        elif kind == "frames":
            intro = f"(In {ex}: now the learner makes {what} - they finish each sentence.) "
        else:
            intro = f"(In {ex}: now {what}.) "
    same = pack.get("same_lang")
    if kind == "review" and same:
        body = (f"Ask which word or phrase from an earlier lesson means \"{it['meaning']}\", and wait - "
                f"the answer is \"{it['text']}\"; do NOT say it yourself. Then STOP.")
    elif kind == "review":
        body = (f"Ask how to say \"{it['meaning']}\" in the language they learn (in {ex}), and wait - "
                f"the answer is \"{it['text']}\"; do NOT say it yourself. Then STOP.")
    elif kind == "build":
        body = (f"Give the task clearly: \"{it['task']}\" - and ask them to say the new sentence "
                f"themselves. Do NOT say the answer (\"{it['answer']}\"). Then STOP.")
    elif kind == "translate":
        body = (f"Say in {ex}: \"{it['en']}\" - and ask them to say it in the language they learn "
                f"themselves. Do NOT say the answer (\"{it['sk']}\"). Then STOP.")
    elif kind == "questions":
        body = (f"Ask the question \"{it['q']}\" slowly, "
                + (f"say what it means in {ex} (\"{it['meaning']}\"), " if it.get("meaning") else "")
                + "and give a model answer they can change: "
                f"\"{it['example']}\". Then ask for THEIR OWN answer and STOP.")
    elif kind in ("words", "collocations", "phrases"):
        body = (f"Say \"{it['text']}\" slowly and clearly, then its meaning in {ex}: "
                f"\"{it['meaning']}\""
                + (f", and the example \"{it['example']}\"" if it.get("example") else "")
                + f". Then: \"{say_it}\" - and \"{it['text']}\" once more.")
    elif kind == "linkers":
        body = (f"Say \"{it['text']}\" - meaning in {ex}: \"{it['meaning']}\". Then the example "
                f"\"{it['example']}\" and what it means in {ex}. Then: \"{say_it} "
                f"{step['expect']}\"")
    elif kind == "grammar":
        body = ((f"Explain the grammar point \"{it.get('name', '')}\" in simple {ex}, in one or two "
                 f"short sentences: {it.get('rule', '')} Point at the board. Then the example "
                 if step["first"] else "Another example of the same grammar: ")
                + f"\"{step['expect']}\""
                + ("" if same else f" (say what it means in {ex}"
                   + (f": \"{it['meanings'][it['examples'].index(step['expect'])]}\""
                      if step["expect"] in (it.get("examples") or []) and it.get("meanings") else "")
                   + ")")
                + f". Then: \"{say_it} {step['expect']}\"")
    elif kind == "extend" and step.get("own"):
        body = (f"Now the learner makes THEIR OWN sentence longer. In {ex}: ask them to say one short "
                "sentence about themselves on this topic, and then the same sentence longer - with "
                "when, where, who with, why or a word they just learned. Give one example, then STOP.")
    elif kind == "extend":
        body = ((f"Show how \"{step['prev']}\" grows ({it.get('how') or 'one more part'}): "
                 if step.get("prev") else "Start with a short sentence: ")
                + f"\"{it['text']}\" (what it means in {ex}). Then: \"{say_it} {it['text']}\"")
    elif kind == "dialogue":
        partner = step.get("partner")
        body = ((f"As the {pack.get('partner_role') or 'partner'}, say \"{partner['text']}\""
                 + (f" and its meaning in {ex} (\"{partner['meaning']}\")" if partner.get("meaning") else "")
                 + ". " if partner else "")
                + f"Then give the learner their line: \"{it['text']}\""
                + (f" - meaning in {ex}: \"{it['meaning']}\"" if it.get("meaning") else "")
                + f". Then \"{say_it}\" and the line once more.")
    else:
        body = (f"Say the frame \"{it['frame']}\" (the gap is a short pause), what it means in "
                f"{ex} (\"{it['meaning']}\"), and what to put in the gap: {it['hint']}. Give the "
                f"example \"{it['example']}\", then ask them to say THEIR OWN sentence.")
    return intro + body


def _teach_show(player, pack: dict, step: dict) -> None:
    _lesson_card(player, _teach_card(pack, step))
    _mode(player, "teach", "" if step.get("open") else step["expect"])


def _teach_begin(player, pack: dict, start: int = 0) -> str | None:
    steps = _teach_steps(pack)
    if not steps:
        return None
    start = start if 0 <= start < len(steps) else 0
    step = dict(steps[start], first=True) if start else steps[0]
    _turn.update(phase="teach", expected=step["expect"], attempts=0, better="",
                 enrich=[], must=[], practice=None)
    _turn["teach"] = {"pack": pack, "steps": steps, "i": start}
    _status_cache["key"] = None
    _teach_show(player, pack, step)
    return _teach_say(pack, step)


def _teach_finish(player) -> str:
    pack = (_turn.get("teach") or {}).get("pack") or {}
    _turn["teach"] = None
    _turn.update(phase="free", expected="", attempts=0, must=[])
    _mode(player, "talk")
    if pack.get("intensive"):
        return _intensive_finish(pack)
    _mark_taught()
    ex = pack.get("explain_in") or _explain_in()
    role = pack.get("partner_role") or ""
    place = role and role.lower() not in ("friend", "a friend", "partner", "colleague")
    return (f"The taught part is finished. In {ex}, say in one short sentence that they did "
            "well and that now they will talk using these words. "
            + (f"Then start a short role play: you are the {role} again, they are themselves - "
               "open it with your first line and give them a hint what to answer. "
               if place else
               "Then ask ONE easy question in the topic and give a model answer they can "
               f"change (\"{_p('for_example')} ...\"), using the words just learned. ")
            + "From now on your job is to get them TALKING about the topic: open "
              "questions, follow-ups (why? what else? tell me more), and ask them to "
              "make short answers longer with the linking words they learned. "
              "Then STOP and wait.")


def _teach_next(prefix: str, player) -> str:
    teach = _turn["teach"]
    teach["i"] += 1
    _turn["attempts"] = 0
    if teach["i"] >= len(teach["steps"]):
        return _next(f"{prefix} {_teach_finish(player)}")
    step = teach["steps"][teach["i"]]
    _turn["expected"] = step["expect"]
    if teach["pack"].get("intensive"):
        _intensive_steps_done(teach["i"])
        _status_cache["key"] = None
    _teach_show(player, teach["pack"], step)
    return _next(f"{prefix} Then the next step of the lesson: {_teach_say(teach['pack'], step)} "
                 "Then STOP and wait for them.")


_QUESTION_RE = re.compile(
    r"\?|^\s*(?:what|why|how|which|can you|could you|i don'?t understand|n[əe] dem[əe]k|"
    r"nə|niy[əe]|nec[əe]|başa düşm|čo|prečo|ako)\b", re.IGNORECASE)


def _fold(text: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", text or "")
                   if unicodedata.category(c) != "Mn")


def _teach_close(said: str, expected: str) -> bool:
    """Close enough to what was taught - accents forgiven: the transcript of a
    beginner's "práca" is often "praca"."""
    import difflib
    a, b = " ".join(an.words(_fold(said))), " ".join(an.words(_fold(expected)))
    letters = difflib.SequenceMatcher(a=a, b=b).ratio() if a and b else 0.0
    return max(_similar(said, expected), _similar(_fold(said), _fold(expected))) >= REPEAT_TEACH \
        or letters >= 0.7


def _teach_turn(text: str, player=None) -> str:
    """The learner answered a step of the taught part."""
    teach = _turn["teach"]
    step = teach["steps"][teach["i"]]
    ex = teach["pack"].get("explain_in") or _explain_in()
    if _QUESTION_RE.search(text or "") and not _teach_close(text, step["expect"]):
        return _next(f'the learner asked something: "{text}". Answer it briefly in simple {ex} '
                     "(one or two sentences), then repeat the current step: "
                     f"{_teach_say(teach['pack'], dict(step, first=False))} Then STOP.")
    if step.get("open"):
        return _teach_frame(text, step, player)
    good = _teach_close(text, step["expect"])
    _repeat_feedback(player, text)
    if good or _turn["attempts"] >= 1:
        prefix = (f"say \"{_p('good')}\"." if good else
                  f"say it once more slowly (\"{step['expect']}\") - no need to repeat, go on.")
        return _teach_next(prefix, player)
    _turn["attempts"] += 1
    return _next(f'not quite - they said "{text}". Say it again slowly, word by word: '
                 f'"{_p("again")} {step["expect"]}" and STOP.')


def _teach_frame(text: str, step: dict, player) -> str:
    """Their own sentence from a frame: checked, fixed once, then on."""
    if _turn["attempts"] >= 1:
        good = _teach_close(text, _turn["expected"])
        return _teach_next(f"say \"{_p('good')}\"." if good else
                           f"say the right sentence once more (\"{_turn['expected']}\") and go on.",
                           player)
    lang = _lang()
    try:
        with _lock:
            ctx = _analysis_ctx(_load(lang), lang)
        result = an.analyse(text, **ctx) or {}
        if _late():
            return None
        _handle(text, player, result=result, react=False)
    except Exception as e:
        _analysis_failed(player, e)
        result = {}
    fixes = result.get("corrections") or []
    if fixes:
        right = result.get("corrected") or step["expect"]
        _turn["attempts"] += 1
        _turn["expected"] = right
        _mode(player, "correct", right)
        why = fixes[0].get("why", "")
        return _next(f'their sentence has a small mistake. Say "{_p("did_you_mean")} {right}", '
                     f"explain why in one short sentence in simple {_explain_in()}"
                     + (f" ({why})" if why else "") + f', then "{_p("now_say_it")} {right}" and STOP.')
    return _teach_next(f"say \"{_p('good')}\" and say their sentence back once, correctly.", player)


def opening_note(player=None) -> str | None:
    """The lesson is starting. In a topic whose taught part has not been given
    yet at this level, the lesson opens with it; None = the usual opening."""
    global _player
    if player is not None:
        _player = player
    if _intensive_on():
        return _intensive_opening(player)
    return None     # the Tutor opens with a greeting: it is free conversation
    lang = _lang()
    with _lock:
        state = _load(lang)
        if _taught(state, lang):
            return None
        topic = _topic_of(state)
        level = _starter_level(state, lang)
    pack = _starter(state, lang, wait=True)
    first = _teach_begin(player, pack) if pack else None
    if not first:
        return None
    ex = pack.get("explain_in") or _explain_in(level)
    return (f"[LESSON_START] Begin the lesson now. You are the teacher. In simple {ex}, greet "
            "the learner in one short sentence and say that today you learn how to talk about "
            f"\"{topic['name']}\": first the words, then a short dialogue, then their own "
            f"sentences. Then the first step: {first} Then STOP and wait for them. Do not call "
            "any tools. Do not read this instruction aloud.")


def _teach_again(player=None) -> str:
    """"Teach me this topic again": the taught part runs once more, now."""
    lang = _lang()
    with _lock:
        state = _load(lang)
    pack = _starter(state, lang, wait=True)
    if not pack:
        return "The lesson for this topic is not ready yet (or this is free talk) - try again soon."
    first = _teach_begin(player or _player, pack)
    return ("The lesson starts again from the words. Say so in one short sentence, then do the "
            f"first step: {first} Then STOP and wait.")


# ── The intensive course ─────────────────────────────────────────────────────
# A second way to learn, next to the topics: a fixed course from zero (for now
# Slovak, 30 days, A1 → A2 - tutor/intensive_slovak.py). The tutor follows its
# material lesson by lesson, step by step, and remembers exactly where the
# learner stopped. It runs on the same step engine as a topic's taught part.

INTENSIVE_COURSES = {"slovak": intensive_slovak.COURSE, "english": intensive_english.COURSE}
# Every language on the Courses page; one without a course yet shows as coming.
COURSE_CATALOG = [("slovak", "Slovak", "A1 → B1"), ("english", "English", "A2 → B1+")]
REVIEW_ITEMS = 4


def _course() -> dict | None:
    return INTENSIVE_COURSES.get(_mode_key())


def _intensive_on() -> bool:
    return str(_setting("track", "normal")) == "intensive" and _course() is not None


def _intensive_load(lang: dict | None = None) -> dict:
    try:
        data = store.get("course_progress", _key(lang or _lang())) or {}
    except Exception:
        data = {}
    data.setdefault("lesson", 0)
    data.setdefault("step", 0)
    data.setdefault("done", [])
    data.setdefault("finished", {})
    return data


def _intensive_save(data: dict, lang: dict | None = None) -> None:
    store.put("course_progress", _key(lang or _lang()), data=data)


def _lesson_open(n: int, prog: dict, idx: int) -> bool:
    """A lesson can be opened when every lesson before it is done - or when it
    is at or before the lesson they are on (a learner who started at A2 may
    still look back at A1)."""
    return n <= max(len(prog.get("done") or []), idx)


def _current_lesson(prog: dict | None = None) -> tuple[int, dict] | None:
    course = _course()
    if not course:
        return None
    prog = prog or _intensive_load()
    idx = max(0, min(int(prog.get("lesson", 0)), len(course["lessons"]) - 1))
    return idx, course["lessons"][idx]


def _review_items(idx: int) -> list[dict]:
    """Words from earlier lessons to recall: two from the last lesson, the rest
    rotating through the older ones."""
    lessons = (_course() or {}).get("lessons", [])[:idx]
    if not lessons:
        return []
    out = list(lessons[-1]["words"][:2])
    older = [w for l in lessons[:-1] for w in l["words"]]
    if older:
        start = (idx * 3) % len(older)
        out += [older[(start + k) % len(older)] for k in range(min(REVIEW_ITEMS - len(out), len(older)))]
    elif len(lessons[-1]["words"]) > 2:
        out += lessons[-1]["words"][2:REVIEW_ITEMS]
    return out[:REVIEW_ITEMS]


def _lesson_pack(idx: int, lesson: dict) -> dict:
    """A course lesson in the shape the step engine teaches."""
    g = lesson["grammar"]
    return {
        "intensive": True, "lesson_index": idx, "name": lesson["title"], "level": lesson["band"],
        "explain_in": _explain_in(lesson["band"]), "partner_role": lesson["partner_role"],
        # An English course is taught in English: no "what it means in English" for its sentences.
        "same_lang": _explain_in(lesson["band"]) == _lang()["name"],
        "review": _review_items(idx),
        "words": [dict(w, example=w.get("example", "")) for w in lesson["words"]],
        "phrases": [dict(p, example="") for p in lesson["phrases"]],
        "grammar": {"name": g["name"], "rule": g["rule"], "table": g.get("table", []),
                    "examples": [sk for sk, _en in g["examples"]],
                    "meanings": [en for _sk, en in g["examples"]], "skills": g.get("skills", [])},
        "dialogue": lesson["dialogue"],
        "translate": lesson.get("translate") or [],
        "extend": lesson.get("extend") or [],
        "build": lesson.get("build") or [],
        "questions": lesson["questions"],
        "speak": lesson["speak"],
    }


def _intensive_plan(idx: int, lesson: dict, lang: dict) -> str:
    course = _course() or {}
    total = len(course.get("lessons", []))
    earlier = [l["title"] for l in course.get("lessons", [])[:idx]]
    return "\n".join([
        f"[LESSON PLAN - {course.get('title', 'INTENSIVE COURSE')}]",
        course.get("learner") or f"The learner started {lang['name']} from ZERO.",
        "This is a course that you follow exactly - never skip its material, never jump ahead.",
        f"Lesson {idx + 1} of {total} (week {lesson['week']}, day {lesson['day']}, {lesson['band']}): "
        f"\"{lesson['title']}\". Goal: {lesson['goal']}.",
        "New words: " + ", ".join(f"{w['text']} ({w['meaning']})" for w in lesson["words"]),
        "Phrases: " + " | ".join(p["text"] for p in lesson["phrases"]),
        f"Grammar: {lesson['grammar']['name']} - {lesson['grammar']['rule']}",
        f"Speaking task after the steps: {lesson['speak']}",
        ("Already learned (use these words freely, they are known): " + "; ".join(earlier))
        if earlier else "Nothing learned before this lesson: use ONLY this lesson's words.",
        "The lesson's steps come one by one in [NEXT] notes: teach exactly the step you are "
        "given, then stop and wait for the learner.",
        "",
    ])


def _intensive_steps_done(i: int) -> None:
    prog = _intensive_load()
    prog["step"] = i
    _intensive_save(prog)


def _intensive_finish(pack: dict) -> str:
    """The lesson's steps are done: record it, move the course on, and turn the
    rest of the session into the speaking task."""
    course = _course() or {}
    prog = _intensive_load()
    idx = int(pack.get("lesson_index", prog.get("lesson", 0)))
    lesson = course["lessons"][idx]
    if lesson["id"] not in prog["done"]:
        prog["done"].append(lesson["id"])
    prog["finished"][lesson["id"]] = time.strftime("%Y-%m-%dT%H:%M:%S")
    last = idx >= len(course["lessons"]) - 1
    prog["lesson"] = idx if last else idx + 1
    prog["step"] = 0
    _intensive_save(prog)
    nxt = "" if last else course["lessons"][idx + 1]["title"]
    ex = pack.get("explain_in") or _explain_in()
    return (f"All the steps of lesson {idx + 1} are done. In {ex}, say in one short sentence that "
            "they did well and name the two most useful things they learned. Then the speaking "
            f"task: {lesson['speak']} Start it now with ONE question or your first line in the "
            "role, using this lesson's words, and give a model answer they can change. From now on "
            "your job is to get them TALKING: follow-up questions, and ask them to make short "
            "answers longer. "
            + (f"When they want to go on, the next lesson is \"{nxt}\" (they say 'next lesson'). "
               if nxt else "This was the last lesson of the course - congratulate them. ")
            + "Then STOP and wait.")


def _intensive_opening(player) -> str | None:
    cur_lesson = _current_lesson()
    if not cur_lesson:
        return None
    idx, lesson = cur_lesson
    prog = _intensive_load()
    pack = _lesson_pack(idx, lesson)
    steps = _teach_steps(pack)
    start = int(prog.get("step", 0))
    start = start if 0 < start < len(steps) else 0
    first = _teach_begin(player, pack, start=start)
    if not first:
        return None
    ex = pack["explain_in"]
    if start:
        hello = (f"In simple {ex}, welcome the learner back in one short sentence and say you "
                 f"continue lesson {idx + 1}, \"{lesson['title']}\", where you stopped.")
    else:
        hello = (f"In simple {ex}, greet the learner in one short sentence. Say this is lesson "
                 f"{idx + 1} of the intensive course, \"{lesson['title']}\", and in one sentence "
                 f"what they will be able to do after it: {lesson['goal']}.")
    return (f"[LESSON_START] Begin the lesson now. You are the teacher. {hello} Then the first "
            f"step: {first} Then STOP and wait for them. Do not call any tools. Do not read this "
            "instruction aloud.")


def set_track(track: str = "normal", player=None) -> tuple[bool, str]:
    """Normal topics or a course - chosen on the page. "intensive:slovak" also
    picks the course's language."""
    raw = str(track).lower()
    track = "intensive" if raw.startswith("int") else "normal"
    wanted = raw.split(":", 1)[1] if ":" in raw else ""
    if track == "intensive":
        key = wanted or (_mode_key() if _mode_key() in INTENSIVE_COURSES else next(iter(INTENSIVE_COURSES)))
        if key not in INTENSIVE_COURSES:
            name = dict((k, n) for k, n, _ in COURSE_CATALOG).get(key, key)
            return False, f"The {name} course is being prepared - coming soon."
        if key != _mode_key():
            ok, message = set_language(cur.LANGUAGES[key]["name"])
            if not ok:
                return False, message
            if str(_setting("track", "normal")) == "intensive":
                reset_lesson()
                _status_cache["key"] = None
                return True, "Course: " + INTENSIVE_COURSES[key]["title"]
    if str(_setting("track", "normal")) == track:
        return True, f"Already in the {track} section."
    _save_setting({"track": track})
    reset_lesson()
    _status_cache["key"] = None
    if track == "intensive":
        return True, "Intensive course: " + (_course() or {}).get("title", "")
    return True, "Normal lessons: topics and free talk."


def goto_lesson(index: int = 0, player=None) -> tuple[bool, str]:
    """Open a lesson from the course map: any lesson already done, or the next one."""
    course = _course()
    if not course:
        return False, "There is no intensive course for this language yet."
    prog = _intensive_load()
    index = int(index)
    reachable = len(prog["done"])
    if not 0 <= index < len(course["lessons"]) or index > reachable:
        return False, "Finish the lessons before it first."
    prog["lesson"], prog["step"] = index, 0
    _intensive_save(prog)
    reset_lesson()
    _status_cache["key"] = None
    if not _intensive_on():
        _save_setting({"track": "intensive"})
    return True, f"Lesson {index + 1}: {course['lessons'][index]['title']}"


def _intensive_next(player=None) -> str:
    """'Next lesson' said to the tutor: the next lesson starts now."""
    cur_lesson = _current_lesson()
    if not cur_lesson:
        return "There is no intensive course for this language."
    idx, lesson = cur_lesson
    if _turn.get("teach"):
        return "The current lesson is not finished yet - carry on with its steps."
    first = _teach_begin(player or _player, _lesson_pack(idx, lesson))
    return (f"Lesson {idx + 1}, \"{lesson['title']}\", starts now. Say so in one short sentence and "
            f"what it is about, then do the first step: {first} Then STOP and wait.")


def _intensive_repeat(player=None) -> str:
    prog = _intensive_load()
    idx, lesson = _current_lesson(prog)
    first = _teach_begin(player or _player, _lesson_pack(idx, lesson))
    return (f"Lesson {idx + 1} starts again from the beginning. Say so in one short sentence, then "
            f"the first step: {first} Then STOP and wait.")


def _language_level(key: str, lang: dict) -> dict:
    """Where the learner is in one language, for the language select:
    "English · B1", "Slovak · A1"."""
    try:
        state = pg.load(_key(lang)) if pg.exists(_key(lang)) else {}
        if not state.get("declared_level"):
            state["declared_level"] = lang.get("start_level") or "A2"
        band, score, _ = pg.effective_level(state)
        if key in INTENSIVE_COURSES and str(_setting("track", "normal")) == "intensive" \
                and key == _mode_key():
            band = _teach_level(state, lang)
        return {"level": band, "score": round(score)}
    except Exception:
        return {"level": lang.get("start_level") or "", "score": 0}


def _intensive_status() -> dict:
    """The course beside the board: every lesson, and the current one's parts
    with the step the learner is on."""
    course = _course() or {}
    prog = _intensive_load()
    idx, lesson = _current_lesson(prog)
    steps = _teach_steps(_lesson_pack(idx, lesson))
    teach = _turn.get("teach") or {}
    live = teach.get("pack", {}).get("intensive") and teach.get("pack", {}).get("lesson_index") == idx
    step = int(teach.get("i", 0)) if live else int(prog.get("step", 0))
    sections: list[dict] = []
    for n, st in enumerate(steps):
        if not sections or sections[-1]["kind"] != st["kind"]:
            sections.append({"kind": st["kind"], "label": _SECTION[st["kind"]][0], "start": n, "count": 0})
        sections[-1]["count"] += 1
    done = set(prog["done"])
    return {"lesson": idx + 1, "title": lesson["title"], "band": lesson["band"],
            "course": course.get("title", ""), "total": len(course.get("lessons", [])),
            "step": step, "steps": len(steps), "sections": sections,
            "lessons": [{"index": n, "week": l["week"], "title": l["title"], "band": l["band"],
                         "state": "done" if l["id"] in done else ("current" if n == idx else "locked"),
                         "open": _lesson_open(n, prog, idx)} for n, l in enumerate(course.get("lessons", []))],
            "weeks": course.get("weeks", [])}


OWN_ANSWER_STEPS = ("review", "translate", "build", "questions", "frames")


def _transcribe_hints() -> list[str] | None:
    """Spelling help for the transcriber - only while the learner repeats
    what they were just given. When the answer is their own (a question about
    their life, a translation, a word to recall), a list of likely words makes
    the transcriber hear the list instead of the learner."""
    teach = _turn.get("teach") or {}
    steps = teach.get("steps") or []
    i = int(teach.get("i", 0))
    if _turn.get("phase") != "teach" or not steps or i >= len(steps):
        return None
    step = steps[i]
    if step.get("open") or step["kind"] in OWN_ANSWER_STEPS:
        return None
    return _hint_words()


def _hint_words() -> list[str]:
    """The words the learner is most likely saying now - handed to the
    transcriber so a beginner's accent is heard as the right word."""
    if _intensive_on():
        idx, lesson = _current_lesson()
        words = [w["text"] for w in lesson["words"]] + [p["text"] for p in lesson["phrases"]]
        return words + [w["text"] for w in _review_items(idx)]
    try:
        lang = _lang()
        with _lock:
            state = _load(lang)
        return [i["text"] for i in _deck(state, lang).get("items", [])]
    except Exception:
        return []


def _intensive_deck(state: dict) -> tuple[dict, list]:
    """The right-hand list in the course: this lesson's words and phrases, and
    words from earlier lessons to review."""
    prog = _intensive_load()
    idx, lesson = _current_lesson(prog)
    done = lesson["id"] in prog["done"]
    lexis = state.get("lexis") or {}
    now = str(_turn.get("expected") or "").lower()

    def row(it: dict, kind: str, learned: bool) -> dict:
        entry = lexis.get(it["text"].lower()) or {}
        return {"text": it["text"], "kind": kind, "meaning": it.get("meaning", ""),
                "native": it.get("native", ""), "uses": int(entry.get("uses", 0)),
                "days": len(entry.get("days") or []) if isinstance(entry.get("days"), list) else 0,
                "stage": 3 if learned else (pg.lexis_stage(entry) if entry else 0),
                "now": bool(now) and it["text"].lower() in now}
    items = ([row(w, "word", done) for w in lesson["words"]]
             + [row(p, "expression", done) for p in lesson["phrases"]])
    due = [row(w, "word", True) for w in _review_items(idx)]
    return {"tier": f"Lesson {idx + 1}", "items": items, "intensive": True,
            "title": lesson["title"]}, due


def end_silence() -> float:
    """Seconds of quiet that end the learner's sentence. A beginner stops to
    find the next word, so the lower the level, the longer the wait."""
    try:
        lang = _lang()
        with _lock:
            level = _teach_level(_load(lang), lang)
    except Exception:
        return 1.1
    return {"A1": 1.9, "A2": 1.6, "B1": 1.3}.get(level, 1.1)


def _course_card(key: str, name: str, levels: str, c: dict) -> dict:
    """What a course list shows of one course."""
    weeks = [dict(w, lessons=[l["title"] for l in c["lessons"] if l["week"] == w["week"]])
             for w in c["weeks"]]
    return {"key": key, "name": name, "levels": levels, "title": c["title"],
            "learner": c.get("about") or c.get("learner", ""), "lessons": len(c["lessons"]),
            "outcomes": c.get("outcomes") or [l["goal"] for l in c["lessons"][::max(1, len(c["lessons"]) // 6)]][:6],
            "words": sum(len(l.get("words") or []) + len(l.get("phrases") or []) for l in c["lessons"]),
            "weeks": weeks}


def _course_progress(key: str, c: dict) -> dict:
    """How far the signed-in learner is in a course (of any language)."""
    prog = _intensive_load(cur.language(key))
    idx = max(0, min(int(prog.get("lesson", 0)), len(c["lessons"]) - 1))
    done = [l for l in c["lessons"] if l["id"] in prog["done"]]
    return {"done": len(done), "total": len(c["lessons"]), "current": idx,
            "current_title": c["lessons"][idx]["title"], "step": int(prog.get("step", 0)),
            "started": bool(done) or idx > 0 or int(prog.get("step", 0)) > 0}


def catalog_for_ui(progress: bool = False) -> dict:
    """Every course of every language, for Home and the course list: its weeks
    and lesson titles - and, for a signed-in learner, how far they are."""
    out = []
    for key, name, levels in COURSE_CATALOG:
        c = INTENSIVE_COURSES.get(key)
        if not c:
            continue
        card = _course_card(key, name, levels, c)
        if progress:
            card["progress"] = _course_progress(key, c)
        out.append(card)
    return {"current": _mode_key() if progress else "", "courses": out,
            "topics": sum(1 for t in tp.TOPICS if not t.get("free"))}


def course_for_ui(key: str) -> dict:
    """One course in full, for its own page: every lesson with its goal and
    words, and the learner's place in it."""
    for k, name, levels in COURSE_CATALOG:
        c = INTENSIVE_COURSES.get(k)
        if k != key or not c:
            continue
        card = _course_card(k, name, levels, c)
        prog = _course_progress(k, c)
        done_ids = set(_intensive_load(cur.language(k))["done"])
        lessons = []
        for n, l in enumerate(c["lessons"]):
            state = ("done" if l["id"] in done_ids else
                     "current" if n == prog["current"] else "locked")
            lessons.append({"index": n, "week": int(l["week"]), "day": int(l["day"]), "band": l["band"],
                            "title": l["title"], "goal": l["goal"], "state": state,
                            "open": n <= max(prog["done"], prog["current"]),
                            "grammar": (l.get("grammar") or {}).get("name", ""),
                            "words": [w["text"] for w in l.get("words") or []],
                            "speak": l.get("speak", "")})
        return dict(card, progress=prog, lessons=lessons, current_language=_mode_key() == k,
                    language=cur.language(k)["name"])
    return {"error": "no such course"}


def intensive_for_ui() -> dict:
    """The course map for the Intensive page."""
    course = _course()
    active = str(_setting("track", "normal")) == "intensive"
    courses = []
    for key, name, levels in COURSE_CATALOG:
        if key != _mode_key():
            continue                # only the courses of the language being learned
        c = INTENSIVE_COURSES.get(key)
        courses.append({"key": key, "name": name, "levels": levels, "available": bool(c),
                        "lessons": len(c["lessons"]) if c else 0,
                        "weeks": len(c["weeks"]) if c else 0,
                        "current": key == _mode_key()})
    if not course:
        return {"available": False, "active": active, "language": _lang()["name"],
                "courses": courses, "languages": [cur.LANGUAGES[k]["name"] for k in INTENSIVE_COURSES]}
    prog = _intensive_load()
    idx = _current_lesson(prog)[0]
    lessons = []
    for n, l in enumerate(course["lessons"]):
        state = ("done" if l["id"] in prog["done"] else
                 "current" if n == idx else "locked")
        parts: list[dict] = []
        for st in _teach_steps(_lesson_pack(n, l)):
            if not parts or parts[-1]["kind"] != st["kind"]:
                parts.append({"kind": st["kind"], "label": _SECTION[st["kind"]][0], "count": 0})
            parts[-1]["count"] += 1
        lessons.append({"index": n, "id": l["id"], "week": l["week"], "day": l["day"],
                        "band": l["band"], "title": l["title"], "goal": l["goal"], "state": state,
                        "open": n <= len(prog["done"]), "words": [w["text"] for w in l["words"]],
                        "phrases": [p["text"] for p in l.get("phrases") or []],
                        "grammar": (l.get("grammar") or {}).get("name", ""),
                        "speak": l.get("speak", ""), "parts": parts,
                        "steps": sum(pt["count"] for pt in parts)})
    steps = lessons[idx]["steps"]
    return {"available": True, "active": active, "language": _lang()["name"], "courses": courses,
            "title": course["title"], "about": course.get("about", ""),
            "levels": next((lv for k, _n, lv in COURSE_CATALOG if k == _mode_key()), ""),
            "outcomes": _course_card(_mode_key(), _lang()["name"], "", course)["outcomes"],
            "words_total": sum(len(l["words"]) + len(l.get("phrases") or []) for l in course["lessons"]),
            "weeks": course["weeks"], "lessons": lessons,
            "current": idx, "step": int(prog.get("step", 0)), "steps": steps,
            "done": len(prog["done"]), "total": len(course["lessons"])}


# ── The conversation, kept per topic ─────────────────────────────────────────
# Every line said - the learner's and the tutor's - is a row of
# conversation_lines (core/store.py), so each topic keeps its whole conversation.

HISTORY_SHOWN = 400


def record_line(who: str, text: str) -> None:
    """One line of the conversation, into the current topic's history."""
    text = str(text or "").strip()
    if not text:
        return
    lang = _lang()
    with _lock:
        topic = "intensive" if _intensive_on() else (_load(lang).get("topic") or tp.DEFAULT_TOPIC)
    store.add_line(_key(lang), tp.slug(topic), who, text[:2000])


def history_for_ui(topic_id: str = "") -> dict:
    """The conversation of one topic (the current one by default), newest last."""
    lang = _lang()
    with _lock:
        state = _load(lang)
    # The course keeps a conversation of its own, apart from the topics.
    topic_id = "intensive" if _intensive_on() else (topic_id or state.get("topic") or tp.DEFAULT_TOPIC)
    return {"topic": topic_id, "lines": store.lines(_key(lang), tp.slug(topic_id), HISTORY_SHOWN)}


def _memory_facts(limit: int = 700) -> str:
    """What LangVis remembers about the learner, short - for example answers
    that are about THEIR life."""
    try:
        from memory.memory_manager import all_entries_for_ui
        facts = [f"{r['key'].replace('_', ' ')}: {r['value']}" for r in all_entries_for_ui()
                 if r.get("category") in ("identity", "preferences", "projects",
                                          "relationships", "wishes")]
    except Exception:
        return ""
    return "; ".join(facts)[:limit]


def answers_for(tutor_turn: str, player=None) -> None:
    """The tutor has just asked a question: put on the board what the learner
    could say back - whole sentences, about THEIR life, ready to say."""
    question = ""
    for part in re.split(r"(?<=[.!?])\s+", tutor_turn.strip()):
        if "?" in part:
            question = part.strip()
    low = tutor_turn.lower()
    # "Did you mean …?" and "say it" want a repeat, not an answer.
    repeat_cues = {"did you mean", "say it", _p("did_you_mean").lower().rstrip(":"),
                   _p("say_it").lower().rstrip(".")}
    if not question or any(c in question.lower() for c in repeat_cues) \
            or any(c in low[-80:] for c in repeat_cues):
        return
    lang = _lang()
    with _lock:
        state = _load(lang)
    level = pg.effective_level(state)[0]
    up = cur.BAND_ORDER[min(cur.band_index(level) + 1, len(cur.BAND_ORDER) - 1)]
    current = _topic_of(state)
    topic = current["name"] + (f" - scenario: {current['prompt'][:300]}" if current.get("prompt") else "")
    prompt = f"""A {level} learner of {lang['name']} must answer their tutor, out loud, in {lang['name']}:
"{question}"
(what the tutor said before it: "{tutor_turn[-300:]}")
Conversation topic: {topic}
What we know about the learner: {_memory_facts() or "nothing yet"}

Write 3 answers they could SAY, each one or two short, natural sentences:
true to what we know about them (if we know nothing, a normal answer anyone
could give), answering exactly this question, in the topic. The first two at
{level}, the third a little richer at {up}. No gaps, no "...", no explanations.
Return ONLY JSON: {{"answers": ["...", "...", "..."]}}"""
    try:
        data = an.parse_json(an.gemini(prompt, json_out=True))
    except Exception as e:
        print(f"[Tutor] answers: {e}")
        return
    answers = [" ".join(str(a).split())[:160] for a in (data.get("answers") or []) if str(a).strip()][:3]
    if answers:
        _send(player or _player, {"type": "answers", "question": question, "answers": answers})


def tutor_said(text: str, player=None) -> None:
    """The tutor finished a turn: the dictionary items it used - topic words,
    upgrades waiting to be learned - were heard once more."""
    _turn["tutor_last"] = str(text or "")[-400:]
    lang = _lang()
    with _lock:
        state = _load(lang)
        waiting = [k for k, e in state.get("lexis", {}).items()
                   if e.get("source") in ("topic", "board") and pg.lexis_stage(e) < 3]
        heard = an.used_items(text, waiting)
        if heard:
            pg.record_exposure(state, heard)
            _save(state, lang, render=False)


def _live_sentence(player, text: str) -> None:
    fn = getattr(player, "send", None)          # the web board, past the live-transcript hold
    if callable(fn):
        try:
            fn({"type": "live_sentence", "text": text, "final": True})
            return
        except Exception:
            pass
    fn = getattr(player, "set_live_sentence", None)
    if callable(fn):
        try:
            fn(text, final=True)
        except Exception:
            pass


def _repeat_feedback(player, text: str) -> None:
    """Show the repeat on the board next to what they were asked to say."""
    fn = getattr(player, "send", None)
    if callable(fn):
        # In a taught step the board must agree with the teacher: the same
        # forgiving check (accents, a word split in two) decides "good".
        teach = _turn["phase"] == "teach"
        fn({"type": "repeat", "text": text, "expected": _turn["expected"],
            "ok": _teach_close(text, _turn["expected"]) if teach else _repeat_ok(text),
            "missing": [] if teach else _missing(text), "phase": _turn["phase"]})


def _analysis_failed(player, error: Exception) -> None:
    """The analyser could not run - usually the free API key's daily limit.
    The tutor keeps talking; the learner is told once why the board is quiet."""
    msg = str(error)
    print(f"[Tutor] analysis failed: {msg[:200]}")
    limited = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower()
    now = time.monotonic()
    if now - _limit_warned[0] < 300:
        return
    _limit_warned[0] = now
    notice = ("The API limit of your Gemini key is reached - the tutor still talks, "
              "but sentences are not checked on the board for now." if limited else
              "A sentence could not be checked - the analyser did not answer.")
    try:
        if player and hasattr(player, "write_log"):
            player.write_log(f"ERR: {notice}")
    except Exception:
        pass
    with _coaching_lock:
        _coaching["notice"] = notice
        _coaching["notice_stamp"] = time.time()


def _board_context(player, text: str, result: dict) -> None:
    """Tell the live tutor, silently, exactly what the board now shows - so the
    better version it says in step 2 is the one on the learner's screen."""
    parts = ["[BOARD] " + _NOT_THE_LEARNER + " Do not reply to this.",
             f'Their last sentence on the board: "{text}"']
    if result["corrections"]:
        parts.append(f'Corrected on the board: "{result["corrected"]}"')
    if result.get("improved"):
        parts.append(f'Better version on the board (use exactly this in step 2): '
                     f'"{result["improved"]}"')
        for e in result.get("enrich", []):
            parts.append(f'  new: "{e["to"]}" ({e["type"]}, {e["level"]}) - {e["meaning"]}')
    _context(player, "\n".join(parts))


def undo_last(player=None) -> tuple[bool, str]:
    """'I didn't say that': take the last analysed sentence back - its score,
    its mistakes, its word counts - if nothing has been recorded since."""
    lang = _lang()
    with _lock:
        if not _last_record:
            return False, "There is nothing to take back."
        state = _load(lang)
        if state.get("totals", {}).get("target_utterances", 0) != _last_record.get("count"):
            return False, "Another sentence was recorded after it - it cannot be taken back now."
        if _last_record.get("raw"):
            store.put("learner_progress", _key(lang), data=_last_record["raw"])
        else:
            store.delete("learner_progress", _key(lang))
        text = _last_record.get("text", "")
        _last_record.clear()
        try:
            pg.render_log(_key(lang), _load(lang), lang)
        except Exception:
            pass
    with _coaching_lock:
        stamp = time.time()
        _coaching.clear()
        _coaching.update(undone=True, said=text, stamp=stamp)
    _say(player or _player,
         "[MISHEARD] " + _NOT_THE_LEARNER + f' The learner says they did NOT say "{text}" '
         "- the transcript was wrong. Say sorry in three words and ask them to say "
         "it again. Forget the correction you made for it.", quiet_for=0.4, user_action=True)
    return True, "Taken back - that sentence no longer counts."


def band_label(score: float) -> str:
    return f"{pg.band(score)} ({score:.0f})"


def _react(player, lang: dict, text: str, result: dict, outcome: dict) -> None:
    """Decide what, if anything, the live tutor needs to hear about."""
    if player is None:
        return
    skills = lang["skills"]

    not_the_learner = (
        "This message is from the tutor system, NOT from the learner - they have "
        "said nothing since your last turn. Never answer it as if they had "
        "spoken, never praise a sentence they did not say, never repeat a "
        "question you already asked, and never end the lesson because of it."
    )

    if outcome["events"]:
        with _lock:
            state = _load(lang)
        _say(player,
             "[TUTOR_PROGRESS] " + not_the_learner + " " + " ".join(outcome["events"])
             + (f" {outcome['band_moved']}" if outcome["band_moved"] else "")
             + "\nCongratulate the learner in ONE short sentence, then continue with "
               "the updated plan below. Never read this tag aloud.\n\n"
             + _lesson_plan(state, lang),
             quiet_for=2.0)
        return

    if outcome["repeated"]:
        with _lock:
            state = _load(lang)
        parts = ["[TUTOR_FOCUS] " + not_the_learner,
                 "The learner keeps making the same kind of mistake."]
        for sid in outcome["repeated"]:
            name, _b, hint = skills[sid]
            ex = state["skills"].get(sid, {}).get("examples", [])[-3:]
            parts.append(f"Skill: {name} ({hint}). Their mistakes: "
                         + "; ".join(f"\"{e['wrong']}\" → \"{e['right']}\"" for e in ex))
        parts.append("When the current exchange is finished, run a 2-minute mini-drill: "
                     "the rule in one simple sentence, one example, then three short "
                     "prompts they must answer out loud using it. Then go back to the "
                     "lesson. Never read this tag aloud.")
        _say(player, "\n".join(parts), quiet_for=2.5)
        return

    if not (result["corrections"] or outcome["band_moved"]):
        return
    gap = _THROTTLE.get(str(_setting("speak_every", "never (log only)")), -1)
    if gap < 0:
        return
    # Only mistakes the course is working on - a target of the current unit or
    # one of the focus skills. Everything else is recorded and reviewed later
    # rather than spoken over the lesson.
    with _lock:
        state = _load(lang)
    wanted = {sid for sid, _ in pg.focus_skills(state, lang)}
    wanted |= set((pg.position(state, lang).get("unit") or {}).get("skills", []))
    result["corrections"] = [c for c in result["corrections"] if c["skill"] in wanted]
    if not (result["corrections"] or outcome["band_moved"]):
        return
    with _lock:
        state = _load(lang)
        now = time.monotonic()
        last = float(state.get("last_spoken") or 0)
        if gap and last and now - last < gap and not outcome["band_moved"]:
            return
        state["last_spoken"] = now
        _save(state, lang, render=False)

    parts = ["[TUTOR_NOTE] " + not_the_learner,
             "Analysis of a sentence the learner said earlier:",
             f'They said: "{text}"']
    for c in result["corrections"]:
        parts.append(f'Mistake: "{c.get("wrong", "")}" → "{c.get("right", "")}" '
                     f'({skills.get(c["skill"], (c["skill"],))[0]}: {c.get("why", "")})')
    if result.get("improved"):
        parts.append(f'Better version: "{result["improved"]}"')
    if outcome["band_moved"]:
        parts.append(f"Milestone: {outcome['band_moved']}")
    parts.append("If you ALREADY corrected this, do not correct it again - continue the "
                 "conversation exactly where it was, without repeating your last "
                 "question. If you did not, correct only the most important mistake "
                 "in one short turn (say it right, ask them to say it), then continue.")
    _say(player, "\n".join(parts), quiet_for=3.0)


def _say(player, instruction: str, quiet_for: float, user_action: bool = False) -> None:
    """Have the tutor speak - only when the learner asked for it (a button, a
    click, a topic). Anything else the tutor system wants said is added as
    context for its next turn: a tutor that starts talking into the silence
    on its own looks like it is answering itself."""
    if not user_action:
        fn = getattr(player, "request_context", None)
        if callable(fn):
            try:
                fn(instruction)
            except Exception:
                pass
        return
    fn = getattr(player, "request_say_when_idle", None)
    if callable(fn):
        try:
            fn(instruction, quiet_for=quiet_for, max_wait=30.0, user_action=True)
            return
        except Exception:
            pass
    fn = getattr(player, "request_say", None)
    if callable(fn):
        try:
            fn(instruction)
        except Exception:
            pass


def _log(player, message: str) -> None:
    try:
        if player and hasattr(player, "write_log"):
            player.write_log(f"SYS: {message}")
        else:
            print(f"[Tutor] {message}")
    except Exception:
        pass


# ── The coaching card ────────────────────────────────────────────────────────
# The board in the middle of the window is this dict, refreshed every time the
# learner says something: their sentence with the wrong parts flagged, the fix,
# the richer version with each new item explained, the grammar that moved, and
# the topic's word list. It is held in memory only - it is about the sentence
# they just said, not about their history.

_coaching: dict = {}
_coaching_lock = threading.Lock()


def _set_coaching(card: dict) -> None:
    with _coaching_lock:
        _coaching.clear()
        _coaching.update(card)
        _coaching["stamp"] = time.time()


def coaching_for_ui() -> dict:
    """The latest board card, plus the topic's list and the words due back."""
    try:
        lang = _lang()
        with _lock:
            state = _load(lang)
        with _coaching_lock:
            card = dict(_coaching)
        if _intensive_on():
            card["deck"], card["due"] = _intensive_deck(state)
            card["lexis"] = pg.lexis_counts(state)
            return card
        deck = _deck(state, lang)
        card["deck"] = deck
        card["due"] = pg.due_lexis(state, exclude={i["text"] for i in deck.get("items", [])})
        card["lexis"] = pg.lexis_counts(state)
        card["unit_title"] = (pg.position(state, lang).get("unit") or {}).get("title", "")
        return card
    except Exception as e:
        print(f"[Tutor] coaching: {e}")
        return {}


def build_card(text: str, result: dict, lang: dict, level: str) -> dict:
    """Turn one analysis into the card. Pure, so it is easy to reason about."""
    corrected = result.get("corrected") or text
    said_tokens, fixed_tokens = an.diff_tokens(text, corrected)
    clean = not result["corrections"]
    fixes = [{"wrong": c.get("wrong", ""), "right": c.get("right", ""),
              "skill_id": c["skill"],
              "skill": lang["skills"].get(c["skill"], (c["skill"],))[0],
              "why": c.get("why", "")} for c in result["corrections"]]
    tip = {}
    if result["corrections"]:
        tip = cur.skill_tip(result["corrections"][0]["skill"], lang["skills"])
    return {
        "said": text,
        "said_tokens": said_tokens,
        "corrected": "" if clean else corrected,
        "fixed_tokens": [] if clean else fixed_tokens,
        "fixes": fixes,
        "clean": clean,
        "praise": result.get("praise", ""),
        "improved": result.get("improved", ""),
        "improved_uses": result.get("improved_uses", []),
        "enrich": result.get("enrich", []),
        "tip": tip,
        "score": round(float(result.get("score", 0))),
        "level": pg.band(float(result.get("score", 0))),
        "spoken_level": level,
    }


# ── UI status ────────────────────────────────────────────────────────────────

_status_cache: dict = {"key": None, "value": {}}


def _topics_list(state: dict) -> list[dict]:
    mine = state.get("topics") or {}
    out = []
    for t in tp.TOPICS:
        out.append({"id": t["id"], "name": t["name"], "az": t["az"],
                    "started": t["id"] in mine, "current": t["id"] == state.get("topic"),
                    "prompt": (mine.get(t["id"]) or {}).get("prompt", "")})
    for tid, entry in mine.items():
        if entry.get("custom"):
            out.append({"id": tid, "name": entry.get("name", tid), "az": entry.get("name", tid),
                        "started": True, "current": tid == state.get("topic"), "custom": True,
                        "prompt": entry.get("prompt", "")})
    return out


def status_for_ui() -> dict:
    """Polled by the interface; re-reads only on change."""
    try:
        lang = _lang()
        key = (lang["name"], store.version("learner_progress"), store.version("topic_materials"),
               time.strftime("%Y-%m-%d"), store.version("course_progress"),
               str(_setting("track", "normal")))
        if _status_cache["key"] != key:
            with _lock:
                state = _load(lang)
                if _ensure_topic(state):
                    _save(state, lang, render=False)
            value = pg.ui_status(state, lang)
            topic = _topic_of(state)
            value["mode"] = lang["name"]
            value["speak"] = _speech_level(state, lang)
            value["modes"] = [dict(_language_level(key, l), name=l["name"], key=key,
                                   enabled=l["enabled"], active=l["name"] == lang["name"])
                              for key, l in cur.LANGUAGES.items()]
            value["topic"] = {"id": topic["id"], "name": topic["name"],
                              "az": topic.get("az", topic["name"])}
            value["topics"] = _topics_list(state)
            value["lexicon_ready"] = tp.load_lexicon(_key(lang), topic["id"]) is not None
            value["track"] = "intensive" if _intensive_on() else "normal"
            if _course():
                value["intensive"] = _intensive_status()
            _status_cache.update(key=key, value=value)
        value = dict(_status_cache["value"])
        topic_id = (value.get("topic") or {}).get("id", "")
        value["lexicon_building"] = tp.is_building(topic_id)
        return value
    except Exception as e:
        print(f"[Tutor] status: {e}")
        return {}


_syllabus_cache: dict = {"key": None, "value": []}


def syllabus_for_ui() -> list:
    """The whole course in order, for the syllabus panel. Same caching as the
    status: re-read only when the learner's file has actually changed."""
    try:
        lang = _lang()
        key = (lang["name"], store.version("learner_progress"))
        if _syllabus_cache["key"] != key:
            with _lock:
                state = _load(lang)
            _syllabus_cache.update(key=key, value=pg.syllabus(state, lang))
        return _syllabus_cache["value"]
    except Exception as e:
        print(f"[Tutor] syllabus: {e}")
        return []


def account_for_ui() -> dict:
    """Everything for the account page."""
    lang = _lang()
    with _lock:
        state = _load(lang)
    data = pg.account(state, lang)
    names = {t["id"]: t["name"] for t in _topics_list(state)}
    for m in data["mistakes"]:
        m["topic_name"] = names.get(m.get("topic", ""), m.get("topic", ""))
    data["topic"] = _topic_of(state)["name"]
    return data


def dictionary_for_ui() -> dict:
    """Every item in the dictionary, for the dictionary page."""
    lang = _lang()
    with _lock:
        state = _load(lang)
    names = {t["id"]: t["name"] for t in _topics_list(state)}
    rows = pg.dictionary_full(state)
    for r in rows:
        # Items from before topics existed carry the analyser's free-text guess.
        r["topic_name"] = names.get(r["topic"], "Before topics")
    return {"items": rows, "counts": pg.lexis_counts(state),
            "topics": sorted({r["topic_name"] for r in rows if r["topic_name"]})}


def set_topic(topic_id: str = "", custom: str = "", player=None,
              prompt: str | None = None, announce: bool = True) -> tuple[bool, str]:
    """Switch the conversation to another topic, from the header or from the
    tutor. `prompt`, when given, is the learner's scenario for the topic ("be a
    barista, I am the customer").

    From the header (`announce=False`) the page starts a new lesson in the
    topic at once - a clean board and a new conversation; the tutor opens it.
    From the tutor's own tool call the lesson carries on in the same session
    and the tutor gets the new plan as a note."""
    global _player
    if player is not None:
        _player = player
    lang = _lang()
    custom = str(custom or "").strip()
    if custom:
        # "travel" said to the tutor is the Travel topic, not a new one.
        low = custom.lower()
        topic = next((t for t in tp.TOPICS if low in (t["id"], t["name"].lower(), t["az"].lower())
                      or low in t["name"].lower().split()), None) or tp.custom_topic(custom)
    else:
        topic = tp.find(str(topic_id or "").strip())
        if topic is None:
            with _lock:
                entry = (_load(lang).get("topics") or {}).get(topic_id)
            if not entry:
                return False, f"There is no topic '{topic_id}'."
            topic = {"id": topic_id, "name": entry.get("name", topic_id),
                     "subtopics": [], "custom": True}
    # A topic belongs to the normal lessons: choosing one leaves the course.
    left_course = _intensive_on()
    if left_course:
        _save_setting({"track": "normal"})
        reset_lesson()
        _status_cache["key"] = None
    with _lock:
        state = _load(lang)
        _ensure_topic(state)
        changed = pg.switch_topic(state, topic["id"], topic["name"],
                                  custom=bool(topic.get("custom"))) or left_course
        new_prompt = False
        if prompt is not None:
            entry = state["topics"][topic["id"]]
            new_prompt = entry.get("prompt", "") != prompt.strip()
            entry["prompt"] = prompt.strip()[:SCENARIO_MAX]
        _save(state, lang)
        scenario = _topic_of(state).get("prompt", "")
        plan = _lesson_plan(state, lang)        # starts writing the word list if needed
        taught = _taught(state, lang)
        _starter(state, lang)                   # …and the topic's first lesson
    if not changed and not new_prompt:
        return True, f"Already talking about {topic['name']}."
    if not announce:
        return True, f"Topic: {topic['name']}" + (" - scenario saved." if new_prompt else ".")
    if not taught:
        opening = opening_note(player or _player)
        if opening:
            _say(player or _player, opening.replace("[LESSON_START]", "[TUTOR_PROGRESS] "
                 + _NOT_THE_LEARNER, 1) + "\n\nUpdated plan:\n\n" + plan,
                 quiet_for=0.6, user_action=True)
            return True, f"Topic: {topic['name']} - the lesson starts with the words."
    start = (f"Start the scene now, in your role: \"{scenario}\". Open it the way that "
             "person would, in one or two short sentences, and hand the learner their first "
             "line with ONE question." if scenario else
             "Say it in one short sentence and ask ONE first question in it.")
    _say(player or _player,
         "[TUTOR_PROGRESS] " + _NOT_THE_LEARNER + f" The learner chose the topic "
         f"\"{topic['name']}\". {start} Updated plan:\n\n" + plan,
         quiet_for=0.6, user_action=True)
    return True, f"Topic: {topic['name']}" + (" - scenario saved." if new_prompt else ".")


def delete_topic(topic_id: str = "", player=None, announce: bool = True) -> tuple[bool, str]:
    """Take a topic off the learner's list. Its words stay in the dictionary -
    they are the learner's - but a topic of their own loses its word list."""
    topic_id = str(topic_id or "").strip()
    if not topic_id or topic_id == tp.DEFAULT_TOPIC:
        return False, "Free talk cannot be deleted."
    lang = _lang()
    with _lock:
        state = _load(lang)
        entry = (state.get("topics") or {}).get(topic_id)
        if entry is None:
            return False, "That topic is not on your list."
        name = entry.get("name", topic_id)
        was_current = state.get("topic") == topic_id
        if was_current:
            free = tp.find(tp.DEFAULT_TOPIC)
            pg.switch_topic(state, free["id"], free["name"])
        state["topics"].pop(topic_id, None)
        _save(state, lang)
    if entry.get("custom"):
        try:
            tp.delete_lexicon(_key(lang), topic_id)
        except Exception:
            pass
    if was_current and announce:
        _say(player or _player, "[TUTOR_PROGRESS] " + _NOT_THE_LEARNER + " The learner "
             f"deleted the topic \"{name}\"; the lesson is back to free talk. Say it in one "
             "short sentence and ask one easy question.", quiet_for=0.4, user_action=True)
    return True, f"Deleted the topic {name}." + (" Back to free talk." if was_current else "")


def start_in_free_talk() -> None:
    """A fresh lesson always opens in free talk; a topic is chosen afterwards."""
    lang = _lang()
    with _lock:
        state = _load(lang)
        free = tp.find(tp.DEFAULT_TOPIC)
        if pg.switch_topic(state, free["id"], free["name"]):
            _save(state, lang, render=False)


def explain_request(item: dict, player=None) -> None:
    """The learner clicked something on the board: have the tutor explain it now."""
    kind = str(item.get("kind") or "")
    script = ""
    if kind == "fix" and item.get("skill_id"):
        board = _board_for(item["skill_id"], said=_turn.get("said", ""),
                           wrong=item.get("wrong", ""), right=item.get("right", ""))
        card = _ai_card(_skill_card(item["skill_id"], mine=[
            {"wrong": item.get("wrong", ""), "right": item.get("right", "")}]), board)
        _lesson_card(player, card)
        script = _board_script(card, item.get("wrong", ""), item.get("right", ""))
    elif kind in ("enrich", "word"):
        _lesson_card(player, _phrase_card(item))
    _mode(player, "explain")
    if kind == "fix" and not item.get("wrong"):
        # A rule picked from the syllabus: teach it, then practise it.
        what = f'the grammar rule "{item.get("skill", "")}" in their syllabus'
        if item.get("skill_id"):
            _turn["practice"] = {"skill": item["skill_id"], "left": PRACTICE_QUESTIONS}
    elif kind == "fix":
        what = (f'the correction "{item.get("wrong", "")}" → "{item.get("right", "")}" '
                f'({item.get("skill", "")})')
    elif kind == "enrich":
        what = (f'the better phrase "{item.get("to", "")}" instead of '
                f'"{item.get("from", "")}" ({item.get("type", "")}, {item.get("level", "")})')
    elif kind == "word":
        what = f'the word "{item.get("text", "")}" from their list'
    else:
        what = f'"{item.get("text", "")}"'
    _say(player or _player,
         "[EXPLAIN] " + _NOT_THE_LEARNER + f" The learner clicked {what} on the board "
         "and wants it explained. Its card is on the board now. You are a teacher at "
         "the board: " + (f"SAY this, slowly, every part of it: \"{script}\"" if script else
         "explain it from the board: what it means, how it is used, one example") +
         " - then ask them to make their own sentence with it and STOP.",
         quiet_for=0.3, user_action=True)


def fluency_request(player=None) -> None:
    _mode(player, "fluency")
    with _lock:
        topic = _topic_of(_load())
    _say(player or _player,
         "[FLUENCY] " + _NOT_THE_LEARNER + f" The learner pressed the fluency button. "
         f"Start a fluency round in the topic \"{topic['name']}\" now, as your "
         "instructions describe.", quiet_for=0.3, user_action=True)


# ── The asked-for half ───────────────────────────────────────────────────────

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action") or "report").strip().lower()
    try:
        if action in ("plan", "lesson", "lesson_plan"):
            return _plan()
        if action in ("weak_points", "weak", "mistakes"):
            return _weak_points()
        if action in ("check", "correct"):
            return _check(parameters.get("text", ""))
        if action in ("practice", "drill", "exercise", "test"):
            return _practice(parameters.get("topic", ""), player)
        if action in ("next_unit", "skip", "skip_unit"):
            return _next_unit()
        if action in ("words", "vocab", "vocabulary"):
            return _words()
        if action in ("pause", "stop"):
            return _set_paused(True)
        if action in ("resume", "start"):
            return _set_paused(False)
        if action in ("set_level", "level"):
            return _set_level(parameters.get("level", ""))
        if action in ("set_goal", "goal"):
            return _set_goal(parameters.get("level", ""))
        if action in ("set_mode", "mode", "language"):
            return _set_mode(parameters.get("mode", ""))
        if action in ("open_log", "open", "log"):
            return _open_log(player)
        if action in ("next_lesson", "continue_course") and _intensive_on():
            return _intensive_next(player)
        if action in ("repeat_lesson", "restart_lesson") and _intensive_on():
            return _intensive_repeat(player)
        if action in ("teach_again", "relearn", "lesson_again", "restart_topic"):
            return _intensive_repeat(player) if _intensive_on() else _teach_again(player)
        if action in ("explain", "board", "teach"):
            return _explain_on_board(parameters.get("topic", "") or parameters.get("text", ""),
                                     player)
        if action in ("set_topic", "topic"):
            ok, message = set_topic(custom=parameters.get("topic", ""), player=player)
            return message + (" The new plan follows as a note." if ok else "")
        return _report()
    except Exception as e:
        return f"The tutor failed: {e}"


def _plan() -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
    return (_lesson_plan(state, lang)
            + "\nContinue teaching from this plan. Do not read it out.")


def _report() -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
    s = pg.ui_status(state, lang)
    delta, arrow = pg.trend(state)
    totals = state.get("totals", {})
    lines = [
        f"{lang['name']} level: {s['level']} ({s['score']}/100)"
        + ("" if s["measured"] else ", still mostly their own estimate") + f". Goal {s['goal']}.",
        f"Course: stage {s['stage']}, unit {s['unit_no']} of {s['unit_total']} "
        f"\"{s['unit_title']}\", {s['unit_progress']}% done.",
        f"Last 7 days: {arrow} {delta:+.1f} points.",
        f"Practice so far: {totals.get('target_utterances', 0)} sentences; "
        f"{s['sentences_today']} today.",
    ]
    if s["focus"]:
        lines.append("Weakest now: " + ", ".join(
            f"{f['name']} ({f['mastery']}/100)" for f in s["focus"]) + ".")
    lines.append("Tell them this in two or three short, simple sentences, at their level.")
    return "\n".join(lines)


def _weak_points() -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
    focus = pg.focus_skills(state, lang, limit=5)
    if not focus:
        return "No repeated weak points yet - not enough has been measured."
    lines = ["Weak points, worst first:"]
    for i, (sid, sk) in enumerate(focus, 1):
        name, _b, hint = lang["skills"][sid]
        ex = sk.get("examples", [])[-1:]
        lines.append(f"{i}. {name} ({hint}) - mastery {pg.mastery(sk)}/100"
                     + (f', e.g. "{ex[0]["wrong"]}" → "{ex[0]["right"]}"' if ex else ""))
    lines.append("Name the top two simply and offer a short drill on the first one.")
    return "\n".join(lines)


def _check(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "Ask the learner to say the sentence they want checked."
    lang = _lang()
    with _lock:
        state = _load(lang)
    unit = pg.position(state, lang).get("unit") or {}
    result = an.analyse(text, language_name=lang["name"], native_language=_native(),
                        level=pg.effective_level(state)[0],
                        unit_title=unit.get("title", ""), unit_skills=unit.get("skills", []),
                        skills=lang["skills"], strictness="strict")
    if not result:
        return f'"{text}" did not read as {lang["name"]}.'
    if not result["corrections"]:
        return f'"{text}" is correct ({band_label(result["score"])}). Confirm it briefly.'
    lines = [f'Checked: "{text}" - {band_label(result["score"])}.']
    for c in result["corrections"]:
        lines.append(f'"{c.get("wrong", "")}" → "{c.get("right", "")}" ({c.get("why", "")})')
    if result.get("improved"):
        lines.append(f'Better: "{result["improved"]}"')
    lines.append("Say the correct sentence, have them repeat it, give the rule in a few words.")
    return "\n".join(lines)


def _practice(topic: str, player=None) -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
    topic = (topic or "").strip().lower()
    sid = None
    if topic:
        for key, (name, _b, _h) in lang["skills"].items():
            if topic in name.lower() or name.lower() in topic or topic.replace(" ", "_") == key:
                sid = key
                break
    if sid is None:
        focus = pg.focus_skills(state, lang, limit=1)
        unit = pg.position(state, lang).get("unit") or {}
        sid = focus[0][0] if focus else (unit.get("skills") or ["past_simple"])[0]
    name, _b, hint = lang["skills"][sid]
    mistakes = [f'"{e["wrong"]}" → "{e["right"]}"'
                for e in state.get("skills", {}).get(sid, {}).get("examples", [])]
    # Build it as one of the unit's real techniques, not as a quiz: the same
    # five minutes spent on a substitution drill and on a multiple-choice test
    # do not teach the same amount.
    unit = pg.position(state, lang).get("unit") or {}
    methods = cur.methods_of(unit) or [cur.method("substitution")]
    technique = methods[0]
    text = an.drill(language_name=lang["name"], native_language=_native(),
                    level=pg.effective_level(state)[0], skill_name=topic or name,
                    hint=hint, mistakes=mistakes,
                    technique=f"{technique['name']}: {technique['how']}")
    if not text:
        return "The drill came back empty - try again."
    try:
        if player and hasattr(player, "show_content"):
            player.show_content(f"Drill - {name}", text)
    except Exception:
        pass
    return (f"Drill on {name} - technique: {technique['name']} ({technique['how']})\n"
            f"{text}\n\nRun it exactly as that technique says. "
            "Give the rule and example, then the prompts ONE "
            "at a time, waiting for each answer and correcting it. Do not read the "
            "answers out. The drill is also on the learner's screen.")


_SKILL_WORDS = {w: "" for w in (
    "tense tenses the a an form forms use using used of and or explain explaining what is are "
    "grammar rule rules please can could you me my i we us it this that these again about tell "
    "teach show help with how do does did difference between mean means meaning when why "
    "let's lets let talk speak practise practice more some bit little izah et edin nədir "
    "nedir oyret öyrət haqqında haqqinda to in on at for from by not no be want need "
    "project work thing things way verb verbs").split()}
_SKILL_WORDS["simple"] = "simple"


def _find_skill(topic: str, lang: dict) -> str | None:
    """Which skill the learner means - "past tense" is the past simple, "the
    perfect" the present perfect. Scored on shared words, the simplest match
    winning a tie."""
    low = str(topic or "").strip().lower()
    if not low:
        return None
    if low.replace(" ", "_") in lang["skills"]:
        return low.replace(" ", "_")
    # A name said as it is - "used to", "would like", "have to" - wins outright,
    # longest first, even when it is made of everyday words.
    said = " " + " ".join(an.words(low)) + " "
    exact = []
    for key, (name, _band, _hint) in lang["skills"].items():
        for phrase in (name.split("(")[0], key.replace("_", " ")):
            words = " ".join(an.words(phrase))
            if len(words.split()) >= 2 and f" {words} " in said:
                exact.append((len(words), key))
    if exact:
        return max(exact)[1]
    want = {w for w in an.words(low) if _SKILL_WORDS.get(w, w)}
    want |= {w[:-1] for w in want if w.endswith("s") and len(w) > 4}   # "conditionals"
    want |= {w + "s" for w in want if len(w) > 3}                      # "modal" → "modals"
    if not want:
        return None
    best, best_key = 0.0, None
    for key, (name, band, hint) in lang["skills"].items():
        have = set(an.words(name)) | set(an.words(key.replace("_", " ")))
        named = len(want & have)
        if not named:
            continue            # the rule itself must be named, not only its example words
        # The closest name wins: "past simple" is the past simple, not
        # "present perfect vs past simple", which only contains it.
        ignore = {"vs", "and", "or", "verb", "verbs"}
        extra = min(len(set(an.words(name)) - want - ignore),
                    len(set(an.words(key.replace("_", " "))) - want - ignore))
        score = named + 0.3 * len(want & set(an.words(hint))) - 0.25 * extra
        # A tie goes to the lower level and the shorter name: "past" alone
        # is the past simple, not the past perfect.
        score -= 0.01 * cur.band_index(band) + 0.001 * len(name)
        if score > best:
            best, best_key = score, key
    return best_key


def _explain_on_board(topic: str, player=None) -> str:
    """The learner asked about a grammar point: draw it on the board and hand
    the tutor what is there, so voice and board teach the same thing."""
    lang = _lang()
    sid = _find_skill(topic, lang)
    if sid is None:
        with _lock:
            unit = pg.position(_load(lang), lang).get("unit") or {}
        sid = (unit.get("skills") or ["present_simple"])[0]
    card = _skill_card(sid)
    _lesson_card(player, card)
    _mode(player, "explain")
    return ("It is on the board now: " + card["title"] + ". Formula: " + " / ".join(card["formula"])
            + ". Rule: " + card["rule"] + " Examples: " + " | ".join(card["examples"])
            + "\nTeach it from the board like a teacher at a whiteboard: the rule in one "
              "sentence, walk through the picture, then 'use it like this' with one example. "
              "Three or four short sentences, then ask them to make their own sentence.")


def _next_unit() -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
        pos = pg.position(state, lang)
        if pos.get("finished"):
            return "The course is already complete."
        if pos.get("unit") is None:
            return ("All units of this stage are done. The stage passes when the level "
                    "reaches the stage goal - keep talking; nothing to skip.")
        events = pg.advance(state, lang, force=True)
        _save(state, lang)
        plan = _lesson_plan(state, lang)
    return (" ".join(events) + " The skipped unit's skills stay on the review list.\n\n"
            + plan + "\nStart the new unit now.")


def _words() -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
    counts = pg.lexis_counts(state)
    deck = _deck(state, lang)
    missing = pg.words_to_reuse(state, limit=6)
    lines = [f"Their dictionary: {counts['learned'] + counts['strong']} items learned, "
             f"{counts['learning']} on the way, {counts['due']} due for review."]
    waiting = [i for i in deck.get("items", []) if i["stage"] < 3]
    if waiting:
        lines.append(f"Topic words still to learn ({deck['tier']}): "
                     + ", ".join(f"{i['text']} ({i['kind']})" for i in waiting[:8]))
    due = pg.due_lexis(state)
    if due:
        lines.append("Old words due back: " + ", ".join(r["text"] for r in due))
    if missing:
        lines.append("Words they needed in their own language: "
                     + ", ".join(f"{k} ({v.get('native', '')})" for k, v in missing))
    lines.append("Name two or three of the waiting ones and put them into a "
                 "question they have to answer with them.")
    return "\n".join(lines)


def _set_paused(paused: bool) -> str:
    lang = _lang()
    with _lock:
        state = _load(lang)
        state["paused"] = paused
        _save(state, lang, render=False)
    return ("Analysis paused: sentences are not measured until resumed. Keep "
            "teaching normally." if paused else "Analysis is back on.")


def _set_level(level: str) -> str:
    level = str(level or "").strip().upper()
    if level not in cur.BAND_ORDER:
        return "Not a CEFR level. Ask for A1, A2, B1, B2, C1 or C2."
    lang = _lang()
    with _lock:
        state = _load(lang)
        state["declared_level"] = level
        # Everything starts again from this level: the measured level, the
        # topic course stage and the course lesson. Words and mistakes stay.
        state["samples"] = []
        state.setdefault("totals", {})["scored"] = 0
        stages = lang.get("stages") or []
        si = next((i for i, st in enumerate(stages)
                   if cur.band_index(st.get("band", "")) >= cur.band_index(level)),
                  max(0, len(stages) - 1))
        state["course"] = dict(pg._empty_course(), stage=si)
        _save(state, lang)
    course = _course()
    if course:
        lessons = course["lessons"]
        first = next((n for n, l in enumerate(lessons)
                      if cur.band_index(l["band"]) >= cur.band_index(level)), len(lessons) - 1)
        prog = _intensive_load(lang)
        prog["lesson"], prog["step"] = first, 0
        _intensive_save(prog, lang)
    _save_setting({"starting_level": level})
    return f"The learner now starts from {level}: level, lessons and course all begin there."


def _set_goal(level: str) -> str:
    level = str(level or "").strip().upper()
    if level not in cur.BAND_ORDER:
        return "Not a CEFR level. Ask for B1, B2 or C1."
    lang = _lang()
    with _lock:
        state = _load(lang)
        state["goal_level"] = level
        _save(state, lang)
    _save_setting({"goal_level": level})
    return f"Goal set to {level}."


def set_language(name: str) -> tuple[bool, str]:
    """Switch course from the UI's language select. Returns (ok, message).

    A mode whose curriculum is not written yet is refused here rather than
    half-applied, so the select can say so and stay on the language that works.
    """
    key = str(name or "").strip().lower().split()[0]
    lang = cur.LANGUAGES.get(key)
    if not lang:
        return False, f"There is no {name} course."
    if not lang["enabled"]:
        return False, f"The {lang['name']} course is not ready yet."
    if key == _mode_key():
        return True, f"Already learning {lang['name']}."
    _save_setting({"mode": lang["name"]})
    _sync_level_setting()
    return True, f"Switched to {lang['name']}."


def _set_mode(mode: str) -> str:
    key = str(mode or "").strip().lower().split()[0] if str(mode or "").strip() else ""
    lang = cur.LANGUAGES.get(key)
    if not lang:
        return "Unknown mode. Available: " + ", ".join(
            l["name"] for l in cur.LANGUAGES.values() if l["enabled"]) + "."
    if not lang["enabled"]:
        return (f"{lang['name']} mode is not available yet - it is coming soon. "
                f"Tell the learner simply, and continue in {_lang()['name']}.")
    _save_setting({"mode": lang["name"]})
    _sync_level_setting()
    return f"Mode is {lang['name']}."


def _sync_level_setting() -> None:
    """Each language keeps its own starting level: after a switch, Settings
    shows the level of the language now being learned."""
    try:
        lang = _lang()
        with _lock:
            level = _load(lang).get("declared_level") or "A1"
        _save_setting({"starting_level": level})
    except Exception as e:
        print(f"[Tutor] level sync failed: {e}")


def _save_setting(values: dict) -> None:
    try:
        from memory.config_manager import save_plugin_config
        save_plugin_config("language_tutor", values)
    except Exception:
        pass


def _open_log(player=None) -> str:
    """The readable progress summary, shown on the page."""
    lang = _lang()
    with _lock:
        report = store.get("learner_reports", _key(lang)) or {}
        text = report.get("markdown") or pg.render_log(_key(lang), _load(lang), lang)
    player = player or _player
    if player is not None and hasattr(player, "show_content"):
        player.show_content(f"{lang['name']} progress", text)
        return "Opened the progress summary on the page."
    return text
