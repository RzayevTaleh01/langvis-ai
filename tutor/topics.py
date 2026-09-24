"""
tutor/topics.py - what the lesson is ABOUT.

The course (tutor/curriculum.py) decides which grammar is being learned; the
topic decides what the conversation is about. The learner picks a topic in the
header, and the whole A2 → B2 grammar ladder is climbed inside it: the same
subject, deeper questions as the level rises.

    A2  describe, routines, simple past events     "What do you do at work every day?"
    B1  experiences, comparisons, plans, problems  "What was your hardest week there?"
    B2  opinions, hypotheticals, arguments         "Should people work from home? Why?"

Each topic owns a FIXED word list - phrasal verbs, collocations, stronger
words and ready expressions - in three level tiers. It is written once, the
first time the topic is opened, saved next to the learner's progress and never
regenerated, so the list on screen does not change under them while they talk.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from tutor import analysis as an

KINDS = ("phrasal", "collocation", "word", "expression")
TIERS = ("A2", "B1", "B2")
ITEMS_PER_TIER = 12

TOPICS: list[dict] = [
    {"id": "free", "name": "Free talk", "az": "Sərbəst söhbət", "subtopics": [], "free": True},
    {"id": "daily_life", "name": "Daily life", "az": "Gündəlik həyat",
     "subtopics": ["morning routine", "weekends", "housework", "sleep and rest",
                   "time management", "habits"]},
    {"id": "work", "name": "Work", "az": "İş",
     "subtopics": ["my job", "colleagues and the boss", "meetings and deadlines",
                   "job interviews", "stress and workload", "working from home"]},
    {"id": "home", "name": "Home", "az": "Ev",
     "subtopics": ["my flat or house", "neighbours", "moving house",
                   "repairs", "rent and bills", "decorating"]},
    {"id": "food", "name": "Food and cooking", "az": "Yemək",
     "subtopics": ["cooking at home", "restaurants", "healthy eating",
                   "national dishes", "shopping for food", "diets"]},
    {"id": "shopping_money", "name": "Shopping and money", "az": "Alış-veriş və pul",
     "subtopics": ["buying clothes", "online shopping", "saving money",
                   "prices and bargains", "returning things", "bank and cards"]},
    {"id": "travel", "name": "Travel", "az": "Səyahət",
     "subtopics": ["airports and flights", "hotels", "planning a trip",
                   "problems on holiday", "sightseeing", "travelling abroad"]},
    {"id": "health", "name": "Health", "az": "Sağlamlıq",
     "subtopics": ["at the doctor", "illness and symptoms", "sport and fitness",
                   "stress and sleep", "healthy lifestyle", "accidents"]},
    {"id": "free_time", "name": "Free time", "az": "Boş vaxt",
     "subtopics": ["hobbies", "films and series", "music", "sport",
                   "games", "going out"]},
    {"id": "people", "name": "Family and friends", "az": "Ailə və dostlar",
     "subtopics": ["my family", "old friends", "making friends",
                   "arguments", "celebrations", "relationships"]},
    {"id": "technology", "name": "Technology", "az": "Texnologiya",
     "subtopics": ["phones and apps", "computers and coding", "social media",
                   "artificial intelligence", "online safety", "gadgets"]},
    {"id": "city", "name": "City and transport", "az": "Şəhər və nəqliyyat",
     "subtopics": ["public transport", "traffic", "my city",
                   "directions", "city vs countryside", "driving"]},
    {"id": "education", "name": "Education", "az": "Təhsil",
     "subtopics": ["school memories", "university", "learning languages",
                   "exams", "online courses", "teachers"]},
    {"id": "opinions", "name": "Opinions and society", "az": "Fikir və cəmiyyət",
     "subtopics": ["news", "environment", "social problems",
                   "the future", "rules and laws", "changes in my country"]},
]

# Every lesson starts in free talk: anything goes, and a topic is a choice.
DEFAULT_TOPIC = "free"

# How deep the questions go at each band. The tutor is handed the line for the
# stage the learner is in, so the topic stays the same and the talk grows up.
DEPTH = {
    "A2": ("describe and report: daily routines, what they have, what they like, "
           "what happened yesterday, simple plans. Questions like 'What do you "
           "usually…?', 'What did you… last…?', 'What are you going to…?'"),
    "B1": ("experiences and stories: 'Have you ever…?', 'Tell me about a time "
           "when…', compare then and now, problems and how they solved them, "
           "plans with reasons, advice"),
    "B2": ("opinions and hypotheticals: 'Should…? Why?', 'What would have "
           "happened if…?', pros and cons, what someone said, arguing a point "
           "and defending it against a counter-argument"),
}

_lock = threading.Lock()
_building: set[str] = set()


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(name or "").strip().lower()).strip("_")
    return s[:40] or "topic"


def find(topic_id: str, custom: dict | None = None) -> dict | None:
    for t in TOPICS:
        if t["id"] == topic_id:
            return t
    if custom and topic_id in custom:
        return custom[topic_id]
    return None


def custom_topic(name: str) -> dict:
    name = str(name or "").strip()[:40]
    return {"id": "custom_" + slug(name), "name": name, "az": name,
            "subtopics": [], "custom": True}


# ── The fixed word list ──────────────────────────────────────────────────────

def has_lexicon(topic: dict) -> bool:
    """Free talk has no fixed list: its words come from the conversation."""
    return not topic.get("free")


def lexicon_path(data_dir: Path, topic_id: str) -> Path:
    return data_dir / "topics" / f"{topic_id}.json"


def load_lexicon(data_dir: Path, topic_id: str) -> dict | None:
    path = lexicon_path(data_dir, topic_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) and data.get("tiers") else None
    except Exception:
        return None


def is_building(topic_id: str) -> bool:
    with _lock:
        return topic_id in _building


def _lexicon_prompt(topic: dict, language_name: str, native_language: str) -> str:
    subs = ", ".join(topic.get("subtopics") or []) or "choose the most useful sub-areas yourself"
    scene = (f"\nThe learner's scenario for it: \"{topic['prompt']}\" - the words must be what "
             "people really say in exactly that situation." if topic.get("prompt") else "")
    return f"""You are writing the vocabulary list of a {language_name} speaking course
for ONE conversation topic: "{topic['name']}" (sub-areas: {subs}).{scene}
The learner's native language is {native_language}.

Write {ITEMS_PER_TIER} items for EACH level tier: A2, B1, B2. The tier is the CEFR
level of the item itself. In each tier aim for about: 4 phrasal verbs, 4
collocations, 2 stronger single words (an upgrade of a plain word), 2 ready
spoken expressions. Everything must be something people really SAY when talking
about this topic, spread across the sub-areas. No rare or literary words, no
grammar terms, no item repeated across tiers.

Return ONLY JSON:
{{
  "tiers": {{
    "A2": [
      {{"text": "run late", "kind": "phrasal | collocation | word | expression",
        "meaning": "very simple English meaning, max 8 words",
        "native": "{native_language} translation",
        "plain": "the plain A2 way to say it that this item upgrades, or empty",
        "example": "one natural example sentence on this topic, max 12 words"}}
    ],
    "B1": [ ... ],
    "B2": [ ... ]
  }}
}}"""


def build_lexicon(data_dir: Path, topic: dict, language_name: str,
                  native_language: str) -> dict | None:
    """Write the topic's list once. Blocking (one model call); returns None on
    failure so the caller can try again later - nothing half-written is saved."""
    tid = topic["id"]
    with _lock:
        if tid in _building:
            return None
        _building.add(tid)
    try:
        existing = load_lexicon(data_dir, tid)
        if existing:
            return existing
        prompt = _lexicon_prompt(topic, language_name, native_language)
        # The bigger model is often "under high demand", and on a free key it
        # allows only a few requests a day; the fast one has its own, larger
        # allowance and writes a perfectly usable list. A long list sometimes
        # comes back as broken JSON - then the other model tries too.
        data = {}
        for model in (an.LESSON_MODEL, an.ANALYSIS_MODEL):
            try:
                data = an.parse_json(an.gemini(prompt, model=model, json_out=True))
            except Exception as e:
                print(f"[Topics] lexicon for {tid} with {model}: {e}")
                data = {}
            if data.get("tiers"):
                break
        tiers = {}
        seen: set[str] = set()
        for tier in TIERS:
            items = []
            for it in (data.get("tiers") or {}).get(tier) or []:
                if not isinstance(it, dict):
                    continue
                text = str(it.get("text") or "").strip().lower()
                if not text or len(text) > 40 or text in seen:
                    continue
                seen.add(text)
                kind = str(it.get("kind") or "word").strip().lower()
                items.append({
                    "text": text,
                    "kind": kind if kind in KINDS else "word",
                    "level": tier,
                    "meaning": str(it.get("meaning") or "")[:80],
                    "native": str(it.get("native") or "")[:60],
                    "plain": str(it.get("plain") or "")[:40],
                    "example": str(it.get("example") or "")[:120],
                })
            tiers[tier] = items[:ITEMS_PER_TIER + 2]
        if sum(len(v) for v in tiers.values()) < 12:
            return None
        lexicon = {"topic": tid, "name": topic["name"], "tiers": tiers}
        path = lexicon_path(data_dir, tid)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(lexicon, indent=2, ensure_ascii=False), encoding="utf-8")
        return lexicon
    except Exception as e:
        print(f"[Topics] lexicon for {tid} failed: {e}")
        return None
    finally:
        with _lock:
            _building.discard(tid)
