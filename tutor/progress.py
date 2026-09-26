"""
tutor/progress.py - everything the tutor knows about the learner.

One row per language (learner_progress in the database, core/store.py) holds:

  samples / days / totals   how well they speak, measured sentence by sentence
  skills                    per-skill evidence: recent right/wrong uses, real
                            mistakes, when to review it next
  course                    where they are in the curriculum
  vocab                     words they had to say in their own language, until
                            they use them in the target language themselves

From that it derives the three things the lesson runs on: the LEVEL (how to
speak to them), the FOCUS (which skills are weakest and must be fixed), and
the PLAN (what this session teaches). progress.md is regenerated from the same
state on every update, so the human file can never drift from the numbers.
"""
from __future__ import annotations

import time
from datetime import date, datetime, timedelta

from core import store
from tutor import curriculum as cur

# ── Measurement constants ────────────────────────────────────────────────────

ROLLING_WINDOW = 25            # sentences in the rolling level
MIN_SAMPLES_FOR_MEASURED = 8   # before this, the stated level is believed
PRIOR_WEIGHT = 20              # the stated level counts as this many sentences…
PRIOR_FADE = 60                # …fading to nothing by this many measured ones
SUBSTANTIVE_WORDS = 5          # shorter sentences are practice, not evidence

SKILL_WINDOW = 12              # recent uses that decide a skill's mastery
REPEAT_ERRORS = 3              # errors in the last 8 uses that trigger a focus drill
FOCUS_NUDGE_GAP = 600          # seconds before the same skill can trigger again
PERSISTENCE_FACTOR = 4         # a unit also passes after 4× the practice at ≥55

FAST_PRACTICE = 4              # a unit whose skills are already strong needs only this

# The dictionary never forgets: every item comes back on this ladder, and a
# strong one still returns once a month. The stage is the number of DIFFERENT
# days it was used correctly - twice in one conversation proves nothing.
LEXIS_LEARNED_DAYS = 3         # distinct days → learned
LEXIS_STRONG_DAYS = 5          # distinct days → strong
LEXIS_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14}   # days in use → days until it returns
LEXIS_STRONG_INTERVAL = 30
MAX_DUE_LEXIS = 5              # old items the tutor is asked to bring back per lesson
MAX_LEXIS_SENTENCES = 3
MAX_MISTAKES = 3000            # the full log behind the account page

MAX_SAMPLES = 600
MAX_DAYS = 180
MAX_DAY_FIXES = 30
MAX_EXAMPLES = 6
MAX_VOCAB = 300
RENDER_DAYS = 30

_BANDS = ((89, "C2"), (74, "C1"), (56, "B2"), (38, "B1"), (20, "A2"), (0, "A1"))
_BAND_MIDPOINT = {"A1": 10.0, "A2": 28.0, "B1": 46.0, "B2": 64.0,
                  "C1": 81.0, "C2": 94.0}


def band(score: float) -> str:
    for floor, name in _BANDS:
        if score >= floor:
            return name
    return "A1"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _today() -> str:
    return date.today().isoformat()


# ── Stored state ─────────────────────────────────────────────────────────────

def _empty_state() -> dict:
    return {
        "version": 2,
        "created": _now_iso(),
        "declared_level": "A1",
        "goal_level": "B2",
        "paused": False,
        "totals": {"utterances": 0, "target_utterances": 0, "native_utterances": 0,
                   "words": 0, "scored": 0},
        "samples": [],
        "days": {},
        "skills": {},
        "lexis": {},        # the dictionary: item -> {kind, uses, offers, topic}
        "deck": [],         # suggestions waiting to be used, freshest first
        "course": _empty_course(),
        "vocab": {},
        "last_spoken": 0.0,
        "topic": "",        # the topic being talked about now
        "topics": {},       # topic id -> {name, course (parked while away), custom}
        "mistakes": [],     # every correction ever made, for the account page
    }


def _empty_course() -> dict:
    return {"stage": 0, "unit": 0, "unit_practice": 0, "unit_started": _now_iso(),
            "completed": [], "finished": False}


def exists(language: str) -> bool:
    """Has this language been studied at all (is there a stored state)?"""
    return store.exists("learner_progress", language)


def load(language: str) -> dict:
    """The learner's state in one language (its lang["data_dir"] key)."""
    try:
        data = store.get("learner_progress", language)
    except Exception as e:
        print(f"[Progress] load failed: {e}")
        data = None
    if not isinstance(data, dict):
        return _empty_state()
    state = _empty_state()
    state.update(data)
    if int(data.get("version", 1)) < 2:
        _migrate_v1(state)
    for entry in state.get("lexis", {}).values():
        _lexis_defaults(entry)
    return state


def save(language: str, state: dict) -> None:
    state["samples"] = state.get("samples", [])[-MAX_SAMPLES:]
    days = state.get("days", {})
    if len(days) > MAX_DAYS:
        for key in sorted(days)[:len(days) - MAX_DAYS]:
            days.pop(key, None)
    state["mistakes"] = state.get("mistakes", [])[-MAX_MISTAKES:]
    vocab = state.get("vocab", {})
    if len(vocab) > MAX_VOCAB:
        for key, _ in sorted(vocab.items(), key=lambda kv: kv[1].get("last", ""))[
                :len(vocab) - MAX_VOCAB]:
            vocab.pop(key, None)
    store.put("learner_progress", language, data=state)


def _migrate_v1(state: dict) -> None:
    """The english_coach file, before the course existed. Its measurements are
    kept whole; its free-text grammar topics become skill evidence, so the
    learner's real weak points are on the focus list from the first lesson."""
    totals = state.setdefault("totals", {})
    totals.setdefault("target_utterances", totals.get("english_utterances", 0))
    totals.setdefault("native_utterances", 0)
    totals.setdefault("scored", sum(
        1 for s in state.get("samples", [])
        if isinstance(s, dict) and int(s.get("words", 0)) >= SUBSTANTIVE_WORDS))

    skills = state.setdefault("skills", {})
    for topic, count in (state.get("topic_totals") or {}).items():
        sid = cur.LEGACY_TOPIC_MAP.get(str(topic).lower())
        if not sid:
            continue
        sk = _skill(skills, sid)
        sk["errors"] += int(count)
        sk["recent"] = ([0] * min(int(count), 4) + sk["recent"])[-SKILL_WINDOW:]

    for key in sorted(state.get("days", {})):
        for c in state["days"][key].get("corrections", []):
            sid = cur.LEGACY_TOPIC_MAP.get(str(c.get("rule", "")).lower())
            if sid:
                _add_example(_skill(skills, sid), c.get("wrong", ""), c.get("right", ""))

    # The learner asked for A2 → B2. A C1 target was the old default.
    if state.get("goal_level") in (None, "", "C1", "C2"):
        state["goal_level"] = "B2"
    state["course"] = state.get("course") or _empty_course()
    state["vocab"] = state.get("vocab") or {}
    state["lexis"] = state.get("lexis") or {}
    state["deck"] = state.get("deck") or []
    state["version"] = 2


# ── Level ────────────────────────────────────────────────────────────────────

def scoring_samples(state: dict, window: int = ROLLING_WINDOW) -> list:
    samples = [s for s in state.get("samples", []) if isinstance(s, dict)]
    substantive = [s for s in samples if int(s.get("words", 0)) >= SUBSTANTIVE_WORDS]
    return (substantive or samples)[-window:]


def effective_level(state: dict) -> tuple[str, float, bool]:
    """(band, score, measured?) - the stated level is a prior worth
    PRIOR_WEIGHT sentences that fades as real evidence accumulates."""
    scoring = scoring_samples(state)
    declared = state.get("declared_level") or "A1"
    prior = _BAND_MIDPOINT.get(declared, 28.0)
    n = len(scoring)
    if not n:
        return declared, prior, False
    fade = max(0.0, 1.0 - int(state.get("totals", {}).get("scored", 0)) / PRIOR_FADE)
    weight = PRIOR_WEIGHT * fade
    mean = sum(float(s.get("score", 0)) for s in scoring) / n
    blended = (prior * weight + mean * n) / (weight + n)
    return band(blended), blended, n >= MIN_SAMPLES_FOR_MEASURED


def _day(state: dict, key: str | None = None) -> dict:
    day = state.setdefault("days", {}).setdefault(key or _today(), {})
    for field, default in (("all_utterances", 0), ("english_utterances", 0),
                           ("native_utterances", 0), ("words", 0),
                           ("score_sum", 0.0), ("score_n", 0), ("best", 0),
                           ("topics", {}), ("corrections", []), ("notes", [])):
        day.setdefault(field, default if not isinstance(default, (dict, list))
                       else type(default)())
    return day


def day_mean(day: dict) -> float:
    n = day.get("score_n") or 0
    return (day.get("score_sum", 0.0) / n) if n else 0.0


def trend(state: dict, days_back: int = 7) -> tuple[float, str]:
    scored = [(k, v) for k, v in sorted(state.get("days", {}).items())
              if (v.get("score_n") or 0) > 0]
    if len(scored) < 2:
        return 0.0, "-"
    latest_key, latest = scored[-1]
    cutoff = (date.fromisoformat(latest_key) - timedelta(days=days_back)).isoformat()
    older = [p for p in scored[:-1] if p[0] <= cutoff] or [scored[0]]
    delta = day_mean(latest) - day_mean(older[-1][1])
    return delta, ("▲" if delta > 1 else "▼" if delta < -1 else "▬")


# ── Skills ───────────────────────────────────────────────────────────────────

def _skill(skills: dict, sid: str) -> dict:
    sk = skills.setdefault(sid, {})
    sk.setdefault("correct", 0)
    sk.setdefault("errors", 0)
    sk.setdefault("recent", [])
    sk.setdefault("examples", [])
    sk.setdefault("last_seen", "")
    sk.setdefault("next_review", "")
    sk.setdefault("nudged", 0.0)
    return sk


def _add_example(sk: dict, wrong: str, right: str) -> None:
    wrong, right = str(wrong or "")[:140], str(right or "")[:140]
    if not right or any(e.get("wrong") == wrong for e in sk["examples"]):
        return
    sk["examples"] = (sk["examples"] + [{"wrong": wrong, "right": right}])[-MAX_EXAMPLES:]


def mastery(sk: dict | None) -> int | None:
    """0-100 from the recent window, errors counting double. None = no evidence."""
    recent = (sk or {}).get("recent") or []
    if not recent:
        return None
    c = sum(recent)
    e = len(recent) - c
    return round(100 * (c + 1) / (c + 2 * e + 2))


def skill_status(sk: dict | None) -> str:
    m = mastery(sk)
    if m is None:
        return "new"
    if m < 50:
        return "weak"
    if m >= cur.SKILL_PASS and sk.get("correct", 0) >= cur.SKILL_MIN_CORRECT:
        return "strong"
    return "learning"


def _schedule_review(sk: dict) -> None:
    status = skill_status(sk)
    streak = 0
    for outcome in reversed(sk["recent"]):
        if outcome != 1:
            break
        streak += 1
    days = {"weak": 1, "learning": 2}.get(status, min(30, 3 * (1 + streak)))
    if sk["recent"] and sk["recent"][-1] == 0:
        days = 0
    sk["next_review"] = (date.today() + timedelta(days=days)).isoformat()


def _use(skills: dict, sid: str, ok: bool) -> dict:
    sk = _skill(skills, sid)
    sk["correct" if ok else "errors"] += 1
    sk["recent"] = (sk["recent"] + [1 if ok else 0])[-SKILL_WINDOW:]
    sk["last_seen"] = _now_iso()
    _schedule_review(sk)
    return sk


# ── Course position ──────────────────────────────────────────────────────────

def position(state: dict, lang: dict) -> dict:
    """Where the learner is: stage, unit (None in consolidation), numbers."""
    course = state.setdefault("course", _empty_course())
    stages = lang["stages"]
    if not stages:
        return {"stage": None, "unit": None, "finished": False}
    si = min(int(course.get("stage", 0)), len(stages) - 1)
    stage = stages[si]
    ui = int(course.get("unit", 0))
    unit = stage["units"][ui] if ui < len(stage["units"]) else None
    return {
        "stage_index": si, "unit_index": ui, "stage": stage, "unit": unit,
        "finished": bool(course.get("finished")),
        "number": cur.unit_number(lang, si, min(ui, len(stage["units"]) - 1)),
        "total": cur.total_units(lang),
        "practice": int(course.get("unit_practice", 0)),
    }


def unit_progress(state: dict, lang: dict) -> tuple[int, list[str]]:
    """(0-100, what is still missing) for the current unit."""
    pos = position(state, lang)
    unit = pos.get("unit")
    if pos.get("finished"):
        return 100, []
    if unit is None:
        stage = pos["stage"]
        score = effective_level(state)[1]
        need = stage["exit_score"]
        missing = [] if score >= need else [f"overall level {score:.0f}/{need}"]
        return min(100, round(100 * score / need)), missing
    missing = []
    need = practice_needed(state, unit)
    parts = [min(1.0, pos["practice"] / need)]
    if pos["practice"] < need:
        missing.append(f"{need - pos['practice']} more sentences")
    for sid in unit["skills"]:
        sk = state.get("skills", {}).get(sid)
        m = mastery(sk) or 0
        correct = (sk or {}).get("correct", 0)
        parts.append(min(1.0, m / cur.SKILL_PASS) * 0.5
                     + min(1.0, correct / cur.SKILL_MIN_CORRECT) * 0.5)
        if skill_status(sk) != "strong":
            name = lang["skills"].get(sid, (sid,))[0]
            missing.append(f"{name}: mastery {m}/{cur.SKILL_PASS}, "
                           f"correct uses {correct}/{cur.SKILL_MIN_CORRECT}")
    return round(100 * sum(parts) / len(parts)), missing


def practice_needed(state: dict, unit: dict) -> int:
    """Sentences a unit needs in the current topic.

    Grammar belongs to the learner, not to the topic: past simple proved while
    talking about work is still proved when they move on to travel. A unit whose
    skills are all already strong only needs a short check in the new topic,
    which is what makes the second topic climb faster than the first.
    """
    skills = state.get("skills", {})
    if unit.get("skills") and all(skill_status(skills.get(sid)) == "strong"
                                  for sid in unit["skills"]):
        return FAST_PRACTICE
    return cur.UNIT_MIN_PRACTICE


def _unit_passed(state: dict, lang: dict, unit: dict) -> bool:
    """A unit is a grammar unit: enough spoken, and every target skill strong.

    Vocabulary is deliberately not a condition - it no longer belongs to a unit
    at all, it belongs to the learner and grows with their own topics.
    """
    practice = int(state["course"].get("unit_practice", 0))
    skills = state.get("skills", {})
    if practice >= practice_needed(state, unit) and all(
            skill_status(skills.get(sid)) == "strong" for sid in unit["skills"]):
        return True
    # Persistence: a skill the analyser rarely sees used should not trap the
    # learner in one unit forever. Plenty of practice at a decent mastery passes.
    return (practice >= cur.UNIT_MIN_PRACTICE * PERSISTENCE_FACTOR and all(
        (mastery(skills.get(sid)) or 0) >= 55 for sid in unit["skills"]))


def advance(state: dict, lang: dict, force: bool = False) -> list[str]:
    """Move through the course as far as the evidence allows. Returns events."""
    events: list[str] = []
    course = state.setdefault("course", _empty_course())
    stages = lang["stages"]
    for _ in range(len(stages) * 6):
        if course.get("finished") or not stages:
            break
        si = course["stage"]
        stage = stages[si]
        ui = course["unit"]
        if ui < len(stage["units"]):
            unit = stage["units"][ui]
            if not (force or _unit_passed(state, lang, unit)):
                break
            force = False
            course["completed"].append(unit["id"])
            course["unit"] = ui + 1
            course["unit_practice"] = 0
            course["unit_started"] = _now_iso()
            if ui + 1 < len(stage["units"]):
                nxt = stage["units"][ui + 1]
                events.append(f"Unit {unit['title']!r} complete. Next unit: "
                              f"{nxt['title']!r}.")
            else:
                events.append(f"Unit {unit['title']!r} complete - every unit of "
                              f"stage {stage['id']} is done. Now: stage review.")
            continue
        if effective_level(state)[1] < stage["exit_score"]:
            break
        if si + 1 >= len(stages):
            course["finished"] = True
            events.append(f"Stage {stage['id']} passed - the whole course "
                          f"(up to {stage['band']}) is complete!")
            break
        course["stage"] = si + 1
        course["unit"] = 0
        course["unit_practice"] = 0
        course["unit_started"] = _now_iso()
        events.append(f"Stage {stage['id']} passed! New stage: "
                      f"{stages[si + 1]['id']} {stages[si + 1]['title']!r}.")
    for e in events:
        note = f"{datetime.now():%H:%M} {e}"
        _day(state)["notes"].append(note)
    return events


# ── Recording ────────────────────────────────────────────────────────────────

def record_target(state: dict, lang: dict, text: str, analysis: dict,
                  n_words: int, used_lexis: list | None = None) -> dict:
    """Fold one analysed target-language sentence into the state."""
    skills = state.setdefault("skills", {})
    day = _day(state)
    before = band(effective_level(state)[1]) if state.get("samples") else ""
    touched = [c["skill"] for c in analysis["corrections"]] + list(analysis["correct_uses"])
    mastery_before = {sid: mastery(skills.get(sid)) for sid in dict.fromkeys(touched)}
    unit_id = ((position(state, lang).get("unit") or {}).get("id", ""))

    state["samples"].append({"ts": _now_iso(), "score": round(analysis["score"], 1),
                             "level": band(analysis["score"]), "words": n_words})
    totals = state.setdefault("totals", {})
    for key, inc in (("utterances", 1), ("target_utterances", 1), ("words", n_words)):
        totals[key] = totals.get(key, 0) + inc
    substantive = n_words >= SUBSTANTIVE_WORDS
    if substantive:
        totals["scored"] = totals.get("scored", 0) + 1
        state["course"]["unit_practice"] = state["course"].get("unit_practice", 0) + 1

    day["all_utterances"] += 1
    day["english_utterances"] += 1
    day["words"] += n_words
    day["score_sum"] += analysis["score"]
    day["score_n"] += 1
    day["best"] = max(day.get("best", 0), round(analysis["score"]))

    repeated: list[str] = []
    now = time.time()
    for c in analysis["corrections"]:
        sid = c["skill"]
        sk = _use(skills, sid, ok=False)
        _add_example(sk, c.get("wrong"), c.get("right"))
        name = lang["skills"].get(sid, (sid,))[0]
        day["topics"][name] = day["topics"].get(name, 0) + 1
        day["corrections"].append({"wrong": str(c.get("wrong", ""))[:160],
                                   "right": str(c.get("right", ""))[:160],
                                   "rule": name, "why": str(c.get("why", ""))[:90]})
        state.setdefault("mistakes", []).append({
            "ts": _now_iso(), "said": text[:300],
            "corrected": str(analysis.get("corrected", ""))[:300],
            "wrong": str(c.get("wrong", ""))[:160], "right": str(c.get("right", ""))[:160],
            "skill": sid, "why": str(c.get("why", ""))[:120],
            "topic": state.get("topic", ""), "unit": unit_id})
        if (sk["recent"][-8:].count(0) >= REPEAT_ERRORS
                and now - float(sk.get("nudged", 0)) > FOCUS_NUDGE_GAP
                and sid not in repeated):
            sk["nudged"] = now
            repeated.append(sid)
    day["corrections"] = day["corrections"][-MAX_DAY_FIXES:]

    for sid in analysis["correct_uses"]:
        _use(skills, sid, ok=True)

    lowered = f" {text.lower()} "
    for key, item in state.setdefault("vocab", {}).items():
        if f" {key} " in lowered:
            item["used"] = item.get("used", 0) + 1
    for w in analysis.get("native_words", []):
        add_vocab(state, w.get("target", ""), w.get("native", ""))

    newly_checked = record_lexis(state, used_lexis or [], text=text,
                                 misused=analysis.get("misused", []))

    events = advance(state, lang)
    after_score = effective_level(state)[1]
    after = band(after_score)
    day["level_score"] = round(after_score, 1)
    band_moved = ""
    if before and after != before:
        up = cur.band_index(after) > cur.band_index(before)
        band_moved = f"Level {'moved up' if up else 'slipped'}: {before} → {after}."
        day["notes"].append(band_moved)

    changes = []
    for sid, was in mastery_before.items():
        now_m = mastery(skills.get(sid))
        if now_m is None or now_m == was:
            continue
        changes.append({"id": sid, "name": lang["skills"].get(sid, (sid,))[0],
                        "before": was if was is not None else 0, "after": now_m})

    return {"score": analysis["score"], "level": after, "band_moved": band_moved,
            "events": events, "repeated": repeated, "checked": newly_checked,
            "skill_changes": changes}


def record_native(state: dict, help_data: dict) -> None:
    totals = state.setdefault("totals", {})
    totals["utterances"] = totals.get("utterances", 0) + 1
    totals["native_utterances"] = totals.get("native_utterances", 0) + 1
    day = _day(state)
    day["all_utterances"] += 1
    day["native_utterances"] += 1
    for w in help_data.get("words", []):
        add_vocab(state, w.get("target", ""), w.get("native", ""))


def record_heard(state: dict) -> None:
    totals = state.setdefault("totals", {})
    totals["utterances"] = totals.get("utterances", 0) + 1
    _day(state)["all_utterances"] += 1


# ── The dictionary ───────────────────────────────────────────────────────────
# Every item the learner meets - the fixed words of their topic, and the
# upgrades the board showed them - lives here for good. Each one counts its
# uses, the DIFFERENT days it was used on, the learner's own sentences with it,
# and when it is due back. Nothing is ever retired: a strong item still
# returns once a month, in whatever topic they are talking about then.

LEXIS_STATUS = ("new", "learning", "learning", "learned", "strong")


def _lexis_defaults(entry: dict) -> dict:
    for field, default in (("kind", "word"), ("uses", 0), ("offers", 0),
                           ("first", _today()), ("topic", ""), ("level", ""),
                           ("meaning", ""), ("native", ""), ("source", ""),
                           ("wrong", 0), ("next_review", ""), ("heard", 0)):
        entry.setdefault(field, default)
    for field in ("days", "sentences", "wrong_sentences"):
        if not isinstance(entry.get(field), list):
            entry[field] = []
    # Files from before the review ladder: one use counts as one day.
    if entry["uses"] and not entry["days"]:
        entry["days"] = [str(entry.get("last") or entry.get("first") or _today())[:10]]
    # …and it goes on the review ladder from its last use, or it would never return.
    if entry["uses"] and not entry["next_review"]:
        try:
            last = date.fromisoformat(entry["days"][-1])
        except ValueError:
            last = date.today()
        entry["next_review"] = (last + timedelta(days=_lexis_interval(entry))).isoformat()
    return entry


def lexis_stage(entry: dict) -> int:
    """0 new · 1-2 learning · 3 learned · 4 strong - by distinct days in use."""
    n = len(entry.get("days") or [])
    if n >= LEXIS_STRONG_DAYS:
        return 4
    if n >= LEXIS_LEARNED_DAYS:
        return 3
    return n


def _lexis_interval(entry: dict) -> int:
    n = len(entry.get("days") or [])
    if n >= LEXIS_STRONG_DAYS:
        return LEXIS_STRONG_INTERVAL
    return LEXIS_INTERVALS.get(n, 14)


def add_lexis(state: dict, item: dict, topic: str = "", source: str = "topic") -> str:
    """Put one item in the dictionary, or fill in what an old entry lacks.
    Returns its key, or '' when the item is unusable."""
    key = str(item.get("text") or "").strip().lower()
    if not key or len(key) > 40:
        return ""
    entry = _lexis_defaults(state.setdefault("lexis", {}).setdefault(key, {}))
    for field in ("level", "meaning", "native", "example"):
        if item.get(field) and not entry.get(field):
            entry[field] = str(item[field])[:120]
    if item.get("kind") and entry["uses"] == 0:
        entry["kind"] = str(item["kind"])
    if topic and not entry.get("topic"):
        entry["topic"] = topic
    if source and not entry.get("source"):
        entry["source"] = source
    return key


def record_lexis(state: dict, used: list, text: str = "",
                 misused: list | None = None) -> list:
    """Count the items used in one sentence, and report what has just become
    learned, so the tutor can acknowledge it once.

    A use on a new day moves the item up the ladder and schedules its return;
    a wrong use counts against it, drops it a step and brings it back today."""
    lexis = state.setdefault("lexis", {})
    today = _today()
    wrong = {str(m).strip().lower() for m in (misused or [])}
    newly = []
    for item in used:
        key = str(item).strip().lower()
        entry = lexis.get(key)
        if entry is None:
            continue
        _lexis_defaults(entry)
        if key in wrong:
            entry["wrong"] += 1
            entry["wrong_sentences"] = (entry["wrong_sentences"] + [text[:200]])[-MAX_LEXIS_SENTENCES:]
            if len(entry["days"]) > 1:
                entry["days"].pop()
            entry["next_review"] = today
            continue
        before = lexis_stage(entry)
        entry["uses"] += 1
        entry["last"] = _now_iso()
        if today not in entry["days"]:
            entry["days"].append(today)
        if text and text[:200] not in entry["sentences"]:
            entry["sentences"] = (entry["sentences"] + [text[:200]])[-MAX_LEXIS_SENTENCES:]
        entry["next_review"] = (date.today() + timedelta(days=_lexis_interval(entry))).isoformat()
        if before < 3 <= lexis_stage(entry):
            entry["learned_on"] = today
            newly.append(key)
    return newly


def _lexis_row(key: str, entry: dict) -> dict:
    stage = lexis_stage(entry)
    return {"text": key, "kind": entry.get("kind", "word"), "level": entry.get("level", ""),
            "meaning": entry.get("meaning", ""), "native": entry.get("native", ""),
            "topic": entry.get("topic", ""), "uses": entry.get("uses", 0),
            "wrong": entry.get("wrong", 0), "days": len(entry.get("days") or []),
            "stage": stage, "status": LEXIS_STATUS[stage],
            "last": str(entry.get("last", ""))[:10], "next_review": entry.get("next_review", ""),
            "sentences": list(entry.get("sentences") or []),
            "wrong_sentences": list(entry.get("wrong_sentences") or []),
            "example": entry.get("example", ""), "source": entry.get("source", ""),
            "heard": entry.get("heard", 0)}


# Words that carry no vocabulary of their own - never dictionary items.
_FUNCTION_WORDS = set("""a an the and or but so if then than because of to in on at by for
with from about into over after before as is am are was were be been being do does did
have has had will would can could should must may might shall i you he she it we they me
him her us them my your his its our their mine yours this that these those there here
what which who whom whose where when why how not no yes very too also just only really
some any all every each much many more most other another such own same one ok okay
um uh yeah oh well like""".split())


def record_vocab(state: dict, items: list, topic: str = "") -> list[str]:
    """The learner's own words: every content word, phrasal verb and chunk
    they said goes into the dictionary (they are counted as uses by the caller).
    Returns the keys, so the caller can count them in this sentence."""
    keys = []
    for raw in items or []:
        text = str(raw or "").strip().lower().strip(".,!?;:\"'")
        parts = text.split()
        if not parts or len(text) > 40 or len(parts) > 4:
            continue
        if len(parts) == 1 and (text in _FUNCTION_WORDS or len(text) < 3 or not text.isalpha()):
            continue
        kind = ("phrasal" if len(parts) == 2 and parts[1] in _PARTICLES else
                "collocation" if len(parts) > 1 else "word")
        key = add_lexis(state, {"text": text, "kind": kind}, topic=topic, source="mine")
        if key:
            keys.append(key)
    return keys


_PARTICLES = {"up", "down", "out", "off", "on", "in", "over", "away", "back", "through",
              "around", "about", "along", "by", "into", "across", "after", "for", "with"}


def record_exposure(state: dict, heard: list) -> None:
    """Items the TUTOR just said: counted as heard - meeting a word in real
    speech is part of learning it, though only the learner's own use moves it."""
    for item in heard:
        entry = state.get("lexis", {}).get(str(item).lower())
        if entry is not None:
            _lexis_defaults(entry)
            entry["heard"] = entry.get("heard", 0) + 1


def sync_topic_all(state: dict, lexicon: dict | None) -> None:
    """Every word of a topic's list is in the dictionary from the moment the
    topic is opened, waiting to be learned - not only the tier on screen."""
    if not lexicon:
        return
    for tier_items in (lexicon.get("tiers") or {}).values():
        for it in tier_items:
            add_lexis(state, it, topic=lexicon.get("topic", ""), source="topic")


def topic_tier(state: dict, lexicon: dict | None, level: str) -> str:
    """The tier on screen: one level above the learner, moving on once most of
    it has been learned - so the words are always a step ahead of them."""
    if not lexicon:
        return ""
    tiers = [t for t in ("A2", "B1", "B2") if (lexicon.get("tiers") or {}).get(t)]
    if not tiers:
        return ""
    want = cur.BAND_ORDER[min(cur.band_index(level) + 1, len(cur.BAND_ORDER) - 1)]
    idx = next((i for i, t in enumerate(tiers) if cur.band_index(t) >= cur.band_index(want)),
               len(tiers) - 1)
    lexis = state.get("lexis", {})
    while idx < len(tiers) - 1:
        items = lexicon["tiers"][tiers[idx]]
        learned = sum(1 for it in items if lexis_stage(lexis.get(it["text"], {})) >= 3)
        if learned < 0.8 * len(items):
            break
        idx += 1
    return tiers[idx]


def sync_topic_deck(state: dict, lexicon: dict | None, level: str) -> list[str]:
    """Make sure every item of the tier on screen is in the dictionary, so a
    use is counted from the very first time. Returns the tier's keys."""
    tier = topic_tier(state, lexicon, level)
    if not tier:
        return []
    keys = []
    for it in lexicon["tiers"][tier]:
        key = add_lexis(state, it, topic=lexicon.get("topic", ""), source="topic")
        if key:
            keys.append(key)
    return keys


def topic_deck(state: dict, lexicon: dict | None, level: str) -> dict:
    """The topic's fixed list for the side panel: same items, same order,
    every time - only the counts change."""
    tier = topic_tier(state, lexicon, level)
    if not tier:
        return {"tier": "", "items": []}
    lexis = state.get("lexis", {})
    items = []
    for it in lexicon["tiers"][tier]:
        row = _lexis_row(it["text"], _lexis_defaults(dict(lexis.get(it["text"]) or {})))
        for field in ("kind", "level", "meaning", "native", "example"):
            row[field] = row.get(field) or it.get(field, "")
        items.append(row)
    return {"tier": tier, "items": items}


def suggested_deck(state: dict, limit: int = 12) -> dict:
    """Free talk has no fixed list: its panel shows the newest words the tutor
    suggested that are not the learner's yet."""
    rows = [(e.get("first", ""), k, e) for k, e in state.get("lexis", {}).items()
            if e.get("source") in ("board", "topic") and lexis_stage(e) < 3]
    rows = sorted(rows, key=lambda r: r[0], reverse=True)[:limit]
    return {"tier": "suggested", "items": [_lexis_row(k, e) for _f, k, e in rows]}


def due_lexis(state: dict, limit: int = MAX_DUE_LEXIS, exclude: set | None = None) -> list[dict]:
    """Old items whose day has come, most overdue first - from any topic."""
    today = _today()
    exclude = exclude or set()
    rows = [(e.get("next_review", ""), k, e) for k, e in state.get("lexis", {}).items()
            if k not in exclude and e.get("uses", 0) > 0
            and e.get("next_review", "") and e["next_review"] <= today]
    rows.sort(key=lambda r: r[0])
    return [_lexis_row(k, e) for _d, k, e in rows[:limit]]


def known_items(state: dict) -> list:
    """Every item in the dictionary, for matching against a new sentence."""
    return list(state.get("lexis", {}).keys())


def lexis_counts(state: dict) -> dict:
    lexis = state.get("lexis", {})
    stages = [lexis_stage(e) for e in lexis.values()]
    return {"total": len(stages),
            "used": sum(1 for e in lexis.values() if e.get("uses", 0) > 0),
            "learning": sum(1 for s in stages if s in (1, 2)),
            "learned": sum(1 for s in stages if s == 3),
            "strong": sum(1 for s in stages if s == 4),
            "due": len(due_lexis(state, limit=10_000))}


def dictionary_full(state: dict) -> list[dict]:
    """Every item, for the dictionary page."""
    rows = [_lexis_row(k, _lexis_defaults(dict(e))) for k, e in state.get("lexis", {}).items()]
    rows.sort(key=lambda r: (-r["uses"], r["text"]))
    return rows


def add_vocab(state: dict, target: str, native: str) -> None:
    key = str(target or "").strip().lower()
    if not key or len(key) > 40:
        return
    item = state.setdefault("vocab", {}).setdefault(
        key, {"native": "", "count": 0, "used": 0, "first": _today()})
    item["native"] = str(native or item.get("native", ""))[:40]
    item["count"] = item.get("count", 0) + 1
    item["last"] = _now_iso()


# ── What to work on ──────────────────────────────────────────────────────────

def focus_skills(state: dict, lang: dict, limit: int = 3) -> list[tuple[str, dict]]:
    """The weakest skills worth fixing now: ones that have gone wrong recently,
    at or below the learner's stage, with the current unit's targets first."""
    pos = position(state, lang)
    if pos.get("stage") is None:
        return []
    in_scope = set(cur.skills_up_to(lang, pos["stage_index"]))
    unit_targets = set((pos.get("unit") or {}).get("skills", []))
    stage_band = cur.band_index(pos["stage"]["band"])
    ranked = []
    for sid, sk in state.get("skills", {}).items():
        if sid not in lang["skills"]:
            continue
        status = skill_status(sk)
        errors = sk.get("recent", []).count(0)
        if status in ("new", "strong") or not errors:
            continue
        skill_band = cur.band_index(lang["skills"][sid][1])
        if sid not in in_scope and sid not in unit_targets and skill_band > stage_band:
            continue            # beyond their level: logged, not drilled
        m = mastery(sk) or 0
        priority = (100 - m) * (1 + errors / 4) + (25 if sid in unit_targets else 0)
        ranked.append((priority, sid, sk))
    ranked.sort(key=lambda r: r[0], reverse=True)
    return [(sid, sk) for _, sid, sk in ranked[:limit]]


def due_reviews(state: dict, lang: dict, limit: int = 2) -> list[str]:
    today = _today()
    focus = {sid for sid, _ in focus_skills(state, lang)}
    due = [sid for sid, sk in state.get("skills", {}).items()
           if sid in lang["skills"] and sid not in focus
           and skill_status(sk) != "new" and sk.get("next_review", "") <= today]
    due.sort(key=lambda sid: state["skills"][sid].get("next_review", ""))
    return due[:limit]


def words_to_reuse(state: dict, limit: int = 6) -> list[tuple[str, dict]]:
    items = [(k, v) for k, v in state.get("vocab", {}).items() if v.get("used", 0) < 2]
    items.sort(key=lambda kv: kv[1].get("last", ""), reverse=True)
    return items[:limit]


# ── The lesson plan ──────────────────────────────────────────────────────────

def lesson_plan(state: dict, lang: dict, native_language: str,
                topic: dict | None = None, deck: dict | None = None,
                depth: str = "") -> str:
    """The plan the tutor teaches from - injected into the session prompt and
    returned by the tool when the plan changes mid-lesson.

    `topic` is what the conversation is about, `deck` its fixed word tier (see
    tutor/topics.py) and `depth` how deep the questions go at this stage."""
    level, score, measured = effective_level(state)
    skills = lang["skills"]
    lines = [f"[LESSON PLAN - {lang['name'].upper()}]",
             f"Goal: {state.get('goal_level', 'B2')}. Learner's native language: "
             f"{native_language}.",
             f"Measured level: {level} ({score:.0f}/100"
             + (")" if measured else ", still mostly their own estimate)") + "."]

    lines += [
        f"Speak to them at {level}. There is NO grammar order to follow: the learner "
        "may bring up any grammar at any time - modal verbs now, the possessive 's in "
        "five minutes - and every rule is measured from what they say. Correct what "
        "comes up; teach what they ask for.",
    ]
    if topic:
        subs = ", ".join(topic.get("subtopics") or [])
        lines += [
            f"TOPIC: \"{topic['name']}\" - the learner chose it. EVERY question you "
            f"ask stays inside this topic"
            + (f"; move between its sub-areas ({subs}) so it never runs dry" if subs
               else "; move between its natural sub-areas so it never runs dry") + ".",
            f"  Question depth at this stage: {depth}" if depth else "",
        ]
    if deck and deck.get("items"):
        waiting = [i for i in deck["items"] if i["stage"] < 3]
        lines.append(f"TOPIC WORDS - the fixed {deck['tier']} list on their screen. Put "
                     "them in your own turns, then ask questions they cannot answer "
                     "well without them. Learned = used on 3 different days:")
        for item in (waiting or deck["items"])[:10]:
            lines.append(f"  \u00b7 {item['text']} ({item['kind']}"
                         + (f", means: {item['meaning']}" if item["meaning"] else "")
                         + f", used {item['uses']}x on {item['days']} day(s))")
    due = due_lexis(state, exclude={i["text"] for i in (deck or {}).get("items", [])})
    if due:
        lines.append("OLD WORDS DUE BACK - learned earlier, maybe in another topic. "
                     "Bring each one back ONCE with a question in THIS topic that "
                     "needs it; if one cannot fit, ask it at the next quiet moment:")
        for item in due:
            lines.append(f"  \u00b7 {item['text']} ({item['kind']}"
                         + (f", from topic {item['topic']}" if item["topic"] else "")
                         + f", used {item['uses']}x)")
    counts = lexis_counts(state)
    lines.append(f"Dictionary so far: {counts['learned'] + counts['strong']} items learned, "
                 f"{counts['learning']} on the way, {counts['total']} in total.")
    lines = [l for l in lines if l]

    focus = focus_skills(state, lang)
    if focus:
        lines.append("FOCUS - their real repeated weak points. Fix these first:")
        for i, (sid, sk) in enumerate(focus, 1):
            name, _b, hint = skills[sid]
            ex = sk.get("examples", [])[-2:]
            shown = "; ".join(f"\"{e['wrong']}\" → \"{e['right']}\"" for e in ex)
            lines.append(f"  {i}. {name} ({hint}) - mastery {mastery(sk)}/100, "
                         f"{sk.get('errors', 0)} mistakes so far."
                         + (f" Their mistakes: {shown}" if shown else ""))
    reviews = due_reviews(state, lang)
    if reviews:
        lines.append("REVIEW due today (use once or twice in conversation): "
                     + ", ".join(skills[s][0] for s in reviews) + ".")
    vocab = words_to_reuse(state)
    if vocab:
        lines.append("WORDS to recycle (they needed these in "
                     f"{native_language}; make them use them): "
                     + ", ".join(f"{k} ({v.get('native', '')})" for k, v in vocab) + ".")
    lines.append("")
    return "\n".join(lines)


# ── The syllabus, as the learner sees it ─────────────────────────────────────

STATUS_ORDER = {"weak": 0, "learning": 1, "new": 2, "strong": 3}


def grammar_syllabus(state: dict, lang: dict) -> list[dict]:
    """The whole grammar syllabus, level by level, each rule with how well the
    learner knows it - measured from their own speech, never asked for.

    There is no order to follow: any rule can come up at any time, and each
    one is measured when it does."""
    skills = state.get("skills", {})
    out = []
    for band, ids in cur.skills_by_band(lang["skills"]).items():
        rows = []
        for sid in ids:
            sk = skills.get(sid)
            name, _b, hint = lang["skills"][sid]
            rows.append({"id": sid, "name": name, "hint": hint,
                         "mastery": mastery(sk), "status": skill_status(sk),
                         "correct": (sk or {}).get("correct", 0),
                         "errors": (sk or {}).get("errors", 0)})
        counts = {k: sum(1 for r in rows if r["status"] == k) for k in STATUS_ORDER}
        out.append({"band": band, "skills": rows, "counts": counts, "total": len(rows)})
    return out


def grammar_summary(state: dict, lang: dict) -> dict:
    rows = [r for band in grammar_syllabus(state, lang) for r in band["skills"]]
    return {"strong": sum(1 for r in rows if r["status"] == "strong"),
            "learning": sum(1 for r in rows if r["status"] == "learning"),
            "weak": sum(1 for r in rows if r["status"] == "weak"),
            "total": len(rows)}


def syllabus(state: dict, lang: dict) -> list[dict]:
    """What the page shows as the syllabus: the grammar, by level."""
    return grammar_syllabus(state, lang)

# ── Topics ───────────────────────────────────────────────────────────────────

def switch_topic(state: dict, topic_id: str, name: str, custom: bool = False) -> bool:
    """Make `topic_id` the topic being talked about. Returns False if it already is.

    Every topic climbs the whole course on its own, so the course position is
    parked with the topic being left and the new topic's own position comes
    back. The very first topic inherits the course the learner already had, so
    nothing measured before topics existed is lost. Skills, level and the
    dictionary are the learner's and are shared by every topic.
    """
    topics = state.setdefault("topics", {})
    current = state.get("topic") or ""
    if current == topic_id:
        return False
    entry = topics.setdefault(topic_id, {"name": name, "custom": bool(custom),
                                         "started": _now_iso()})
    entry["name"] = name
    if current:
        topics.setdefault(current, {"name": current})["course"] = state.get("course")
        state["course"] = entry.get("course") or _empty_course()
    entry.pop("course", None)       # the live position is state["course"]
    entry["last"] = _now_iso()
    state["topic"] = topic_id
    return True


def topic_positions(state: dict, lang: dict) -> list[dict]:
    """How far each topic has climbed, for the account page."""
    out = []
    for tid, entry in state.get("topics", {}).items():
        course = state["course"] if tid == state.get("topic") else entry.get("course")
        pos = position({"course": dict(course or _empty_course())}, lang)
        stage = pos.get("stage") or {}
        out.append({"id": tid, "name": entry.get("name", tid), "current": tid == state.get("topic"),
                    "stage": stage.get("id", "-"), "band": stage.get("band", ""),
                    "unit_no": pos.get("number", 0), "unit_total": pos.get("total", 0),
                    "unit_title": (pos.get("unit") or {}).get("title", "Stage review"),
                    "finished": pos.get("finished", False),
                    "done": len((course or {}).get("completed", []))})
    out.sort(key=lambda t: (not t["current"], -t["done"], t["name"]))
    return out


# ── The account page ─────────────────────────────────────────────────────────

def account(state: dict, lang: dict) -> dict:
    """Everything the account page draws: level, its history, every grammar
    skill with its evidence, the mistake log, the dictionary's growth, topics."""
    level, score, measured = effective_level(state)
    totals = state.get("totals", {})
    mistakes = state.get("mistakes", [])
    days = sorted(state.get("days", {}).items())

    history = []
    for key, d in days:
        if not d.get("score_n"):
            continue
        value = d.get("level_score") or day_mean(d)
        history.append({"date": key, "score": round(float(value), 1),
                        "sentence_score": round(day_mean(d), 1),
                        "sentences": d.get("english_utterances", 0),
                        "mistakes": sum(1 for m in mistakes if m.get("ts", "")[:10] == key)
                        or len(d.get("corrections", []))})

    per_skill: dict[str, int] = {}
    for m in mistakes:
        per_skill[m.get("skill", "")] = per_skill.get(m.get("skill", ""), 0) + 1

    skills = []
    for sid, (name, sband, hint) in lang["skills"].items():
        sk = state.get("skills", {}).get(sid)
        tip = cur.skill_tip(sid, lang["skills"])
        skills.append({
            "id": sid, "name": name, "band": sband, "hint": hint,
            "mastery": mastery(sk), "status": skill_status(sk),
            "correct": (sk or {}).get("correct", 0),
            "errors": (sk or {}).get("errors", 0),
            "logged_errors": per_skill.get(sid, 0),
            "examples": list((sk or {}).get("examples", []))[-4:],
            "next_review": (sk or {}).get("next_review", ""),
            "rule": tip.get("rule", ""), "rule_examples": tip.get("examples", []),
        })

    learned_by_day: dict[str, int] = {}
    for e in state.get("lexis", {}).values():
        # learned_on from before the review ladder meant "used twice"; only
        # items learned under today's rule (3 different days) are counted.
        if e.get("learned_on") and lexis_stage(e) >= 3:
            learned_by_day[e["learned_on"]] = learned_by_day.get(e["learned_on"], 0) + 1
    growth, running = [], 0
    for key in sorted(set(learned_by_day) | {k for k, _ in days}):
        running += learned_by_day.get(key, 0)
        growth.append({"date": key, "learned": running})

    return {
        "level": level, "score": round(score, 1), "measured": measured,
        "goal": state.get("goal_level", "B2"), "declared": state.get("declared_level", "A2"),
        "totals": {"sentences": totals.get("target_utterances", 0),
                   "words": totals.get("words", 0),
                   "native": totals.get("native_utterances", 0),
                   "mistakes": len(mistakes) or sum(s.get("errors", 0)
                                                    for s in state.get("skills", {}).values()),
                   "days": len(days)},
        "lexis": lexis_counts(state),
        "history": history[-120:],
        "growth": growth[-120:],
        "skills": skills,
        "mistakes": list(reversed(mistakes[-400:])),
        "syllabus": grammar_syllabus(state, lang),
        "bands": {"A2": 20, "B1": 38, "B2": 56, "C1": 74},
    }


# ── UI snapshot ──────────────────────────────────────────────────────────────

def ui_status(state: dict, lang: dict) -> dict:
    level, score, measured = effective_level(state)
    return {
        "level": level, "score": round(score), "measured": measured,
        "goal": state.get("goal_level", "B2"),
        "grammar": grammar_summary(state, lang),
        "focus": [{"name": lang["skills"][sid][0], "mastery": mastery(sk) or 0}
                  for sid, sk in focus_skills(state, lang)],
        "sentences_today": _day(state).get("english_utterances", 0),
        "lexis": lexis_counts(state),
        "paused": bool(state.get("paused")),
    }


# ── The markdown log ─────────────────────────────────────────────────────────

def _cell(value) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ").strip()


def render_log(language: str, state: dict, lang: dict) -> str:
    level, score, measured = effective_level(state)
    pos = position(state, lang)
    delta, arrow = trend(state)
    totals = state.get("totals", {})
    progress, missing = unit_progress(state, lang)
    unit = pos.get("unit")

    out = [f"# {lang['name']} progress", "",
           "_Written by LangVis. Regenerated on every update - edits by hand are "
           "overwritten; the database holds the raw numbers._", "",
           "## Where you are", "",
           f"- **Level:** **{level}** ({score:.0f}/100)"
           + ("" if measured else " - still mostly your own estimate"),
           f"- **Goal:** {state.get('goal_level', 'B2')}",
           f"- **Stage:** {(pos.get('stage') or {}).get('id', '-')} "
           f"{(pos.get('stage') or {}).get('title', '')}",
           f"- **Unit:** {pos.get('number')}/{pos.get('total')} - "
           + ("course complete" if pos.get("finished") else
              f"{unit['title']} ({progress}%)" if unit else f"stage review ({progress}%)"),
           f"- **Last 7 days:** {arrow} {delta:+.1f} points",
           f"- **Practised:** {totals.get('target_utterances', 0)} sentences, "
           f"{totals.get('words', 0)} words; fell back to your own language "
           f"{totals.get('native_utterances', 0)} times"]
    counts = lexis_counts(state)
    out += ["", f"**Dictionary:** {counts['learned'] + counts['strong']} learned "
                f"({counts['strong']} strong), {counts['learning']} in progress, "
                f"{counts['due']} due for review", ""]
    for row in dictionary_full(state)[:40]:
        if row["uses"]:
            out.append(f"- {'[x]' if row['stage'] >= 3 else '[ ]'} {row['text']} "
                       f"({row['kind']}) \u2014 used {row['uses']}x on {row['days']} day(s)")
    if missing:
        out += ["", "**To finish this unit:** " + "; ".join(missing)]

    focus = focus_skills(state, lang, limit=5)
    if focus:
        out += ["", "## Focus now", ""]
        for sid, sk in focus:
            out.append(f"- **{lang['skills'][sid][0]}** - mastery {mastery(sk)}/100, "
                       f"{sk.get('errors', 0)} mistakes")
            for e in sk.get("examples", [])[-2:]:
                out.append(f"  - ~~{_cell(e.get('wrong'))}~~ → {_cell(e.get('right'))}")

    rows = [(sid, sk) for sid, sk in state.get("skills", {}).items() if sid in lang["skills"]]
    if rows:
        rows.sort(key=lambda r: (mastery(r[1]) or 0))
        out += ["", "## Skills", "", "| Skill | Level | Mastery | Right | Wrong | Status |",
                "| --- | --- | --- | --- | --- | --- |"]
        for sid, sk in rows:
            name, b, _ = lang["skills"][sid]
            out.append(f"| {name} | {b} | {mastery(sk) or 0} | {sk.get('correct', 0)} "
                       f"| {sk.get('errors', 0)} | {skill_status(sk)} |")

    vocab = words_to_reuse(state, limit=20)
    if vocab:
        out += ["", "## Words to use", ""]
        out += [f"- **{k}** - {v.get('native', '')}" for k, v in vocab]

    out += ["", "## Daily record", ""]
    days = sorted(state.get("days", {}).items(), reverse=True)[:RENDER_DAYS]
    for key, day in days:
        if not (day.get("score_n") or day.get("native_utterances")):
            continue
        mean = day_mean(day)
        out += [f"### {key} - {band(mean)} ({mean:.0f}/100)", "",
                f"- {day.get('english_utterances', 0)} sentences, "
                f"{day.get('words', 0)} words, best {day.get('best', 0)}/100, "
                f"own language {day.get('native_utterances', 0)} times."]
        out += [f"- {n}" for n in day.get("notes", [])]
        corrections = day.get("corrections", [])
        if corrections:
            out += ["", "| You said | Better | Skill |", "| --- | --- | --- |"]
            out += [f"| {_cell(c.get('wrong'))} | {_cell(c.get('right'))} "
                    f"| {_cell(c.get('rule'))} |" for c in corrections]
        out += [""]

    text = "\n".join(out).rstrip() + "\n"
    store.put("learner_reports", language, data={"markdown": text})
    return text
