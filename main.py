"""
main.py - start LangVis.

    python main.py            starts the local server and opens http://localhost:8765/
    python main.py --no-open  starts the server only
    python main.py --port 8766  on another port
"""
import sys

# ── Console encoding ─────────────────────────────────────────────────────────
# Status lines carry emoji and arrows. On a non-UTF-8 console - cp1254 on a
# Turkish Windows, cp1251 on a Russian one - printing one raises
# UnicodeEncodeError from inside the session and takes it down.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Watch our own output ─────────────────────────────────────────────────────
# Installed before anything can print, so no traceback escapes unrecorded.
# Wrapped deliberately: logging must never be what stops the app from starting.
try:
    from core import selflog as _selflog
    _selflog.install()
except Exception as _e:                                  # pragma: no cover
    print(f"[SelfLog] disabled: {_e}")

from web.server import main as serve  # noqa: E402  (after the console is set up)

if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else None
    serve(open_browser="--no-open" not in sys.argv, port=port)
