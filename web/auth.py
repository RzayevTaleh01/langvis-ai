"""
web/auth.py - accounts: sign up, sign in, sign out.

The accounts live in PostgreSQL (docker-compose.yml). A password is stored
only as a scrypt hash; a signed-in browser holds a random session token in an
HttpOnly cookie, and the database only keeps the token's SHA-256.

    POST /api/auth/register   {name, email, password, learning}
    POST /api/auth/login      {email, password}
    POST /api/auth/logout
    GET  /api/auth/me         -> {user: {...} | null}

Everything else under /api/ and /ws needs a signed-in account (see
web/server.py, _require_account).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg
from aiohttp import web

COOKIE = "langvis_session"
SESSION_DAYS = 30
MIN_PASSWORD = 8
LANGUAGES = ("English", "Slovak")

# A few wrong passwords in a row, then a pause: nobody guesses a password here.
MAX_FAILS = 5
FAIL_WINDOW = 600       # seconds

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    learning      TEXT NOT NULL DEFAULT 'English',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_user_id ON sessions(user_id);
"""


def database_url() -> str:
    """DATABASE_URL from the environment, else from .env, else the default
    of docker-compose.yml."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, value = line.strip().partition("=")
            if key == "DATABASE_URL" and value:
                return value.strip().strip('"').strip("'")
    return "postgresql://langvis:langvis@127.0.0.1:5433/langvis"


# ── Passwords ────────────────────────────────────────────────────────────────

_N, _R, _P = 2 ** 14, 8, 1


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return f"scrypt${_N}${_R}${_P}${b64(salt)}${b64(digest)}"


def check_password(password: str, stored: str) -> bool:
    try:
        kind, n, r, p, salt, digest = stored.split("$")
        if kind != "scrypt":
            return False
        want = base64.b64decode(digest)
        got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt),
                             n=int(n), r=int(r), p=int(p), dklen=len(want))
        return hmac.compare_digest(got, want)
    except Exception:
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def public(user) -> dict:
    """What the page may know about an account."""
    return {"id": user["id"], "name": user["name"], "email": user["email"],
            "learning": user["learning"],
            "created_at": user["created_at"].isoformat() if user["created_at"] else None}


class Accounts:
    """The database, and the account handlers of the server."""

    def __init__(self, on_signed_in, on_signed_out) -> None:
        # Set by the server: an account has signed in / out in some browser.
        self.on_signed_in = on_signed_in        # async (user, created: bool, first: bool) -> None
        self.on_signed_out = on_signed_out      # async (user_id) -> None
        self.pool: asyncpg.Pool | None = None
        self._fails: dict[str, list[float]] = {}

    async def open(self, _app=None) -> None:
        url = database_url()
        last = None
        for _ in range(10):         # the container may still be starting
            try:
                self.pool = await asyncpg.create_pool(url, min_size=1, max_size=5)
                break
            except Exception as e:
                last = e
                await asyncio.sleep(1)
        if self.pool is None:
            raise SystemExit(f"❌ The accounts database is not reachable ({last}).\n"
                             f"   Start it first:  docker compose up -d")
        async with self.pool.acquire() as con:
            await con.execute(SCHEMA)
            await con.execute("DELETE FROM sessions WHERE expires_at < now()")
        print("⚙  Accounts database ready.")

    async def close(self, _app=None) -> None:
        if self.pool is not None:
            await self.pool.close()

    # ── Who is this browser ──────────────────────────────────────────────────

    async def user_of(self, request: web.Request):
        """The signed-in account of the request, or None."""
        token = request.cookies.get(COOKIE)
        if not token or self.pool is None:
            return None
        return await self.pool.fetchrow(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = $1 AND s.expires_at > now()", _token_hash(token))

    async def _start_session(self, user_id: int, response: web.Response) -> None:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
        await self.pool.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES ($1, $2, $3)",
            _token_hash(token), user_id, expires)
        await self.pool.execute("UPDATE users SET last_login_at = now() WHERE id = $1", user_id)
        response.set_cookie(COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True,
                            samesite="Lax", path="/")

    # ── Handlers ─────────────────────────────────────────────────────────────

    async def me(self, request: web.Request) -> web.Response:
        user = await self.user_of(request)
        return web.json_response({"user": public(user) if user else None})

    async def register(self, request: web.Request) -> web.Response:
        body = await _body(request)
        name = " ".join(str(body.get("name") or "").split())[:40]
        email = str(body.get("email") or "").strip().lower()
        password = str(body.get("password") or "")
        learning = str(body.get("learning") or "English")
        if not name:
            return _error("Please write your name.")
        if not _EMAIL.match(email) or len(email) > 200:
            return _error("That does not look like an email address.")
        if len(password) < MIN_PASSWORD:
            return _error(f"The password needs at least {MIN_PASSWORD} characters.")
        if learning not in LANGUAGES:
            learning = "English"
        hashed = await asyncio.to_thread(hash_password, password)
        async with self.pool.acquire() as con:
            async with con.transaction():
                first = await con.fetchval("SELECT count(*) FROM users") == 0
                try:
                    user = await con.fetchrow(
                        "INSERT INTO users (email, name, password_hash, learning) "
                        "VALUES ($1, $2, $3, $4) RETURNING *", email, name, hashed, learning)
                except asyncpg.UniqueViolationError:
                    return _error("There is already an account with this email. Log in instead.")
        response = web.json_response({"ok": True, "user": public(user)})
        await self._start_session(user["id"], response)
        await self.on_signed_in(user, True, first)
        return response

    async def login(self, request: web.Request) -> web.Response:
        body = await _body(request)
        email = str(body.get("email") or "").strip().lower()
        password = str(body.get("password") or "")
        key = f"{email}|{request.remote}"
        now = time.monotonic()
        fails = [t for t in self._fails.get(key, []) if now - t < FAIL_WINDOW]
        if len(fails) >= MAX_FAILS:
            return _error("Too many wrong passwords. Please wait a few minutes.", 429)
        user = await self.pool.fetchrow("SELECT * FROM users WHERE email = $1", email)
        ok = user is not None and await asyncio.to_thread(check_password, password,
                                                          user["password_hash"])
        if not ok:
            self._fails[key] = fails + [now]
            return _error("Wrong email or password.", 401)
        self._fails.pop(key, None)
        response = web.json_response({"ok": True, "user": public(user)})
        await self._start_session(user["id"], response)
        await self.on_signed_in(user, False, False)
        return response

    async def logout(self, request: web.Request) -> web.Response:
        token = request.cookies.get(COOKIE)
        user = await self.user_of(request)
        if token:
            await self.pool.execute("DELETE FROM sessions WHERE token_hash = $1", _token_hash(token))
        response = web.json_response({"ok": True})
        response.del_cookie(COOKIE, path="/")
        if user is not None:
            await self.on_signed_out(user["id"])
        return response


async def _body(request: web.Request) -> dict:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


def _error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)
