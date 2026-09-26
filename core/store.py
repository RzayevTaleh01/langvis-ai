"""
core/store.py - every piece of LangVis data, in PostgreSQL.

Nothing an account learns is kept in files any more: settings, memory, the
learner's progress, the course position, the topic word lists and lessons, and
every line of every conversation are rows in the database of
docker-compose.yml (the same one that holds the accounts, web/auth.py).

    app_settings        the Gemini keys - shared by every account on this computer
    user_settings       an account's names, voice and tutor settings
    user_memory         what LangVis remembers about the learner
    learner_progress    per language: level, skills, dictionary, mistakes
    learner_reports     per language: the readable progress summary
    course_progress     per language: current lesson, step, finished lessons
    topic_materials     per language and topic: the word list, the first lesson
    conversation_lines  every line said, per language and topic

The tutor's code is synchronous and runs in worker threads, so this module
talks to the database synchronously (psycopg) over one connection, behind a
lock. Reads are served from a small in-process cache that every write keeps
up to date - there is one server process, so the cache is never stale.

Without a signed-in account (a script, a test) nothing is persisted: the
values live in memory for the life of the process.
"""
from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path

import psycopg

from core import profile

SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS user_settings (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS user_memory (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS learner_progress (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, language)
);
CREATE TABLE IF NOT EXISTS learner_reports (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, language)
);
CREATE TABLE IF NOT EXISTS course_progress (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, language)
);
CREATE TABLE IF NOT EXISTS topic_materials (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    topic_id   TEXT NOT NULL,
    kind       TEXT NOT NULL,
    level      TEXT NOT NULL DEFAULT '',
    data       JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, language, topic_id, kind, level)
);
CREATE TABLE IF NOT EXISTS conversation_lines (
    id         BIGSERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    language   TEXT NOT NULL,
    topic      TEXT NOT NULL,
    who        TEXT NOT NULL,
    text       TEXT NOT NULL,
    said_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversation_lines_topic
    ON conversation_lines (user_id, language, topic, id);
"""

# table -> the columns that identify one row (user_id first where there is one)
_KEYS: dict[str, tuple[str, ...]] = {
    "app_settings": ("key",),
    "user_settings": ("user_id",),
    "user_memory": ("user_id",),
    "learner_progress": ("user_id", "language"),
    "learner_reports": ("user_id", "language"),
    "course_progress": ("user_id", "language"),
    "topic_materials": ("user_id", "language", "topic_id", "kind", "level"),
}
_PER_USER = {t for t, cols in _KEYS.items() if cols[0] == "user_id"}

_lock = threading.RLock()
_conn: psycopg.Connection | None = None
_url: str | None = None
_cache: dict[tuple, str | None] = {}         # (table, *key) -> JSON text, None = no row
_memory_only: dict[tuple, str] = {}          # without an account
_versions: dict[str, int] = {}               # table -> writes so far (for the callers' caches)
_lines_memory: list[dict] = []


# ── The connection ───────────────────────────────────────────────────────────

def open(url: str) -> None:            # noqa: A001 - the module's own verb
    """Connect and create the tables. Called once at start, after the accounts
    table exists (web/auth.py)."""
    global _url
    _url = url
    with _lock:
        _connect().execute(SCHEMA)
    print("⚙  Data store ready.")


def close() -> None:
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None


def ready() -> bool:
    return _url is not None


def _connect() -> psycopg.Connection:
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg.connect(_url, autocommit=True)
    return _conn


def _run(sql: str, params: tuple = ()) -> list[tuple]:
    """One statement; a dropped connection is opened again once."""
    with _lock:
        for attempt in (0, 1):
            try:
                cur = _connect().execute(sql, params)
                return cur.fetchall() if cur.description else []
            except psycopg.OperationalError:
                close()
                if attempt:
                    raise
    return []


# ── Documents: one JSON value per row ────────────────────────────────────────

def _user(user_id: int | None) -> int | None:
    return profile.current() if user_id is None else user_id


def _full_key(table: str, key: tuple, user_id: int | None) -> tuple | None:
    if table not in _KEYS:
        raise KeyError(table)
    if table in _PER_USER:
        uid = _user(user_id)
        key = (uid,) + tuple(key)
    if len(key) != len(_KEYS[table]):
        raise ValueError(f"{table} needs {_KEYS[table]}")
    return key


def _persisted(table: str, full: tuple) -> bool:
    return ready() and not (table in _PER_USER and full[0] is None)


def get(table: str, *key, user_id: int | None = None):
    """The stored value, or None. Every call returns a fresh copy."""
    full = _full_key(table, key, user_id)
    with _lock:
        if not _persisted(table, full):
            text = _memory_only.get((table,) + full)
        elif (table,) + full in _cache:
            text = _cache[(table,) + full]
        else:
            where = " AND ".join(f"{c} = %s" for c in _KEYS[table])
            rows = _run(f"SELECT data::text FROM {table} WHERE {where}", full)
            text = rows[0][0] if rows else None
            _cache[(table,) + full] = text
    return None if text is None else json.loads(text)


def exists(table: str, *key, user_id: int | None = None) -> bool:
    return get(table, *key, user_id=user_id) is not None


def put(table: str, *key, data, user_id: int | None = None) -> None:
    full = _full_key(table, key, user_id)
    text = json.dumps(data, ensure_ascii=False, default=str)
    with _lock:
        if not _persisted(table, full):
            _memory_only[(table,) + full] = text
        else:
            cols = _KEYS[table]
            _run(f"INSERT INTO {table} ({', '.join(cols)}, data, updated_at) "
                 f"VALUES ({', '.join(['%s'] * len(cols))}, %s::jsonb, now()) "
                 f"ON CONFLICT ({', '.join(cols)}) DO UPDATE "
                 f"SET data = EXCLUDED.data, updated_at = now()", full + (text,))
            _cache[(table,) + full] = text
        _versions[table] = _versions.get(table, 0) + 1


def delete(table: str, *key, user_id: int | None = None) -> None:
    full = _full_key(table, key, user_id)
    with _lock:
        if not _persisted(table, full):
            _memory_only.pop((table,) + full, None)
        else:
            where = " AND ".join(f"{c} = %s" for c in _KEYS[table])
            _run(f"DELETE FROM {table} WHERE {where}", full)
            _cache[(table,) + full] = None
        _versions[table] = _versions.get(table, 0) + 1


def version(table: str) -> int:
    """Grows with every write to the table - a cheap "has it changed?"."""
    with _lock:
        return _versions.get(table, 0)


def forget_user_cache() -> None:
    """Another account is in use: nothing of the last one stays in memory."""
    with _lock:
        _cache.clear()
        _memory_only.clear()
        _lines_memory.clear()
        for table in _versions:
            _versions[table] += 1


# ── The conversation ─────────────────────────────────────────────────────────

def add_line(language: str, topic: str, who: str, text: str,
             user_id: int | None = None) -> None:
    uid = _user(user_id)
    if not ready() or uid is None:
        with _lock:
            _lines_memory.append({"language": language, "topic": topic, "who": who, "text": text})
        return
    _run("INSERT INTO conversation_lines (user_id, language, topic, who, text) "
         "VALUES (%s, %s, %s, %s, %s)", (uid, language, topic, who, text))


def lines(language: str, topic: str, limit: int, user_id: int | None = None) -> list[dict]:
    """The last `limit` lines of a conversation, oldest first."""
    uid = _user(user_id)
    if not ready() or uid is None:
        with _lock:
            rows = [l for l in _lines_memory if l["language"] == language and l["topic"] == topic]
        return [{"ts": "", "who": l["who"], "text": l["text"]} for l in rows[-limit:]]
    rows = _run("SELECT to_char(said_at, 'YYYY-MM-DD\"T\"HH24:MI:SS'), who, text FROM ("
                "  SELECT id, said_at, who, text FROM conversation_lines "
                "  WHERE user_id = %s AND language = %s AND topic = %s "
                "  ORDER BY id DESC LIMIT %s) last ORDER BY id",
                (uid, language, topic, limit))
    return [{"ts": ts, "who": who, "text": text} for ts, who, text in rows]


# ── The files of earlier versions, moved into the database once ──────────────

def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _import_language_dir(uid: int, language: str, folder: Path) -> None:
    level = _read_json(folder / "level.json")
    if isinstance(level, dict) and get("learner_progress", language, user_id=uid) is None:
        put("learner_progress", language, data=level, user_id=uid)
    course = _read_json(folder / "intensive.json")
    if isinstance(course, dict) and get("course_progress", language, user_id=uid) is None:
        put("course_progress", language, data=course, user_id=uid)
    for path in sorted((folder / "topics").glob("*.json")):
        data = _read_json(path)
        if not isinstance(data, dict):
            continue
        parts = path.stem.split(".starter.")
        kind, level_key = ("starter", parts[1]) if len(parts) == 2 else ("lexicon", "")
        if get("topic_materials", language, parts[0], kind, level_key, user_id=uid) is None:
            put("topic_materials", language, parts[0], kind, level_key, data=data, user_id=uid)
    for path in sorted((folder / "history").glob("*.jsonl")):
        rows = []
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                line = json.loads(raw)
            except Exception:
                continue
            if isinstance(line, dict) and line.get("text"):
                rows.append((uid, language, path.stem, str(line.get("who") or ""),
                             str(line["text"])[:2000], line.get("ts") or None))
        with _lock:
            for row in rows:
                _run("INSERT INTO conversation_lines (user_id, language, topic, who, text, said_at) "
                     "VALUES (%s, %s, %s, %s, %s, COALESCE(%s::timestamptz, now()))", row)


def import_account_files(uid: int, folder: Path, languages: tuple[str, ...]) -> list[str]:
    """Move an account's files (or the ones from before accounts existed) into
    the database, then delete them. Returns what was moved."""
    moved = []
    for language in languages:
        if (folder / language).is_dir():
            _import_language_dir(uid, language, folder / language)
            moved.append(str(folder / language))
    memory = _read_json(folder / "memory" / "long_term.json")
    if isinstance(memory, dict) and get("user_memory", user_id=uid) is None:
        put("user_memory", data=memory, user_id=uid)
        moved.append(str(folder / "memory" / "long_term.json"))
    settings = _read_json(folder / "settings.json")
    if isinstance(settings, dict) and get("user_settings", user_id=uid) is None:
        put("user_settings", data=settings, user_id=uid)
        moved.append(str(folder / "settings.json"))
    for path in moved:
        p = Path(path)
        shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return moved


def import_shared_config(path: Path, user_keys: tuple[str, ...]) -> bool:
    """config/api_keys.json of earlier versions: its keys into app_settings."""
    data = _read_json(path)
    if not isinstance(data, dict):
        return False
    if get("app_settings", "config") is None:
        put("app_settings", "config", data={k: v for k, v in data.items() if k not in user_keys})
    own = {k: data[k] for k in user_keys if k in data}
    if own and get("app_settings", "unclaimed_user_settings") is None:
        # names, voice and tutor settings from before accounts: the first account takes them
        put("app_settings", "unclaimed_user_settings", data=own)
    path.unlink(missing_ok=True)
    return True
