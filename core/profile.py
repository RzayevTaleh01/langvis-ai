"""
core/profile.py - whose data is in use.

Every account keeps its own progress, course position, dictionary, history,
memory and settings under users/u<id>/. There is one microphone and one voice
session, so one account is in use at a time: the server switches it when
another account signs in (web/server.py).

Without an account (a script, a test) everything lives where it always did,
next to the code.
"""
from __future__ import annotations

import shutil
import sys
import threading
from pathlib import Path


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE = _base_dir()
USERS_DIR = BASE / "users"

_lock = threading.Lock()
_user_id: int | None = None

# What a learner had before accounts existed: handed to the first account.
LEGACY_DIRS = ("english", "slovak")
LEGACY_MEMORY = Path("memory") / "long_term.json"


def current() -> int | None:
    with _lock:
        return _user_id


def set_user(user_id: int | None) -> None:
    global _user_id
    with _lock:
        _user_id = user_id
    if user_id is not None:
        user_dir(user_id).mkdir(parents=True, exist_ok=True)


def user_dir(user_id: int | None = None) -> Path:
    """The folder of an account's data - the account in use when none is given."""
    uid = current() if user_id is None else user_id
    return BASE if uid is None else USERS_DIR / f"u{uid}"


def memory_path() -> Path:
    return user_dir() / LEGACY_MEMORY


def settings_path(user_id: int | None = None) -> Path | None:
    """An account's own settings file (the one in use when none is given);
    None without an account."""
    uid = current() if user_id is None else user_id
    return None if uid is None else user_dir(uid) / "settings.json"


def adopt_legacy_data(user_id: int) -> list[str]:
    """The very first account gets the progress made before accounts existed.
    Copied, not moved: the old files stay as they were. Returns what was copied."""
    target = user_dir(user_id)
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in LEGACY_DIRS:
        src = BASE / name
        if src.is_dir() and not (target / name).exists():
            shutil.copytree(src, target / name)
            copied.append(name)
    src = BASE / LEGACY_MEMORY
    if src.is_file() and not (target / LEGACY_MEMORY).exists():
        (target / LEGACY_MEMORY).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target / LEGACY_MEMORY)
        copied.append(str(LEGACY_MEMORY))
    return copied
