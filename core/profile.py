"""
core/profile.py - whose data is in use.

Every account keeps its own progress, course position, dictionary, history,
memory and settings - rows of its own in the database (core/store.py). There
is one microphone and one voice session, so one account is in use at a time:
the server switches it when another account signs in (web/server.py).
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE = _base_dir()
# Where earlier versions kept each account's files - moved into the database
# on start (web/server.py) and then deleted.
USERS_DIR = BASE / "users"
# What a learner had before accounts existed: moved to the first account.
LEGACY_DIRS = ("english", "slovak")

_lock = threading.Lock()
_user_id: int | None = None


def current() -> int | None:
    with _lock:
        return _user_id


def set_user(user_id: int | None) -> None:
    global _user_id
    with _lock:
        _user_id = user_id
