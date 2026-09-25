import json
import sys
from pathlib import Path

from core import profile


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR    = get_base_dir()
CONFIG_DIR  = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "api_keys.json"

# ── Two files ────────────────────────────────────────────────────────────────
# The Gemini keys belong to the computer: config/api_keys.json, shared by every
# account. Names, voice and the tutor's settings belong to the learner: with an
# account signed in they live in users/u<id>/settings.json (core/profile.py).
# Without one, everything stays in api_keys.json as it always did.
USER_KEYS = ("assistant_name", "user_name", "voice_name", "plugin_config")


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _read(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"❌ Failed to load {path.name}: {e}")
        return {}


def load_api_keys() -> dict:
    """Every setting in force: the shared ones, and the account's own on top."""
    data = _read(CONFIG_FILE)
    user_file = profile.settings_path()
    if user_file is not None:
        mine = _read(user_file)
        for key in USER_KEYS:
            data.pop(key, None)
            if key in mine:
                data[key] = mine[key]
    return data


def _write(data: dict) -> None:
    """Store `data` (a whole load_api_keys() dict): the account's own keys to
    its file, the rest to the shared one."""
    ensure_config_dir()
    user_file = profile.settings_path()
    if user_file is None:
        CONFIG_FILE.write_text(json.dumps(data, indent=4), encoding="utf-8")
        return
    shared = _read(CONFIG_FILE)
    shared.update({k: v for k, v in data.items() if k not in USER_KEYS})
    CONFIG_FILE.write_text(json.dumps(shared, indent=4), encoding="utf-8")
    mine = {k: data[k] for k in USER_KEYS if k in data}
    user_file.parent.mkdir(parents=True, exist_ok=True)
    user_file.write_text(json.dumps(mine, indent=4, ensure_ascii=False), encoding="utf-8")


def _patch_config(**fields) -> None:
    """Read-modify-write one or more keys. Every setter goes through here, so
    there is one place where a corrupt file is handled."""
    data = load_api_keys()
    data.update(fields)
    _write(data)


def save_api_keys(gemini_api_key: str) -> None:
    _patch_config(gemini_api_key=gemini_api_key.strip())


def get_gemini_key() -> str | None:
    return load_api_keys().get("gemini_api_key")


def get_gemini_keys() -> list[str]:
    """Every key, the main one first. The spare keys take over when a key has
    used up its free daily limit."""
    data = load_api_keys()
    keys = [data.get("gemini_api_key") or ""] + list(data.get("gemini_extra_keys") or [])
    return [k for k in dict.fromkeys(str(k).strip() for k in keys) if len(k) > 15]


def set_gemini_keys(main: str, extras: list[str]) -> None:
    main = str(main or "").strip()
    _patch_config(gemini_api_key=main,
                  gemini_extra_keys=[k for k in dict.fromkeys(str(x).strip() for x in extras)
                                     if len(k) > 15 and k != main])

def is_configured() -> bool:
    key = get_gemini_key()
    return bool(key and len(key) > 15)


def get_assistant_name() -> str:
    """Return the configured assistant name, or 'LangVis' if not set."""
    return load_api_keys().get("assistant_name", "LangVis") or "LangVis"


def get_user_name() -> str:
    """Return the configured user name for addressing."""
    return load_api_keys().get("user_name", "")


def save_assistant_config(assistant_name: str, user_name: str) -> None:
    """Persist assistant name and user name to config."""
    _patch_config(assistant_name=assistant_name.strip() or "LangVis",
                  user_name=user_name.strip())


# ── Assistant voice ──────────────────────────────────────────────────────────
# Gemini Live prebuilt voices. Names are proper nouns - identical in every
# language, so this list is safe to show verbatim in any locale.
AVAILABLE_VOICES = ["Charon", "Puck", "Kore", "Fenrir", "Aoede"]
DEFAULT_VOICE    = "Charon"


def get_voice() -> str:
    """Return the configured Live voice, falling back to the default if unset
    or if the stored value is not a voice we recognise."""
    v = load_api_keys().get("voice_name", DEFAULT_VOICE) or DEFAULT_VOICE
    return v if v in AVAILABLE_VOICES else DEFAULT_VOICE


def save_voice(voice_name: str) -> None:
    """Persist the chosen Live voice. Unknown names collapse to the default so a
    bad value can never reach the API and break the session."""
    v = (voice_name or "").strip()
    _patch_config(voice_name=v if v in AVAILABLE_VOICES else DEFAULT_VOICE)


def get_plugin_enabled(plugin_name: str) -> bool:
    """Plugins are enabled by default the moment they're discovered (opt-out model)."""
    return load_api_keys().get("plugins_enabled", {}).get(plugin_name, True)


# ── Per-plugin settings ("tokens" / connection details) ───────────────────────
# Generic store so a plugin can declare its own config fields (PLUGIN_SETTINGS)
# and the settings UI renders + persists them WITHOUT any core edit - keeping the
# drop-in model intact. Values live under plugin_config[<namespace>][<key>].
# A namespace defaults to the plugin name, but a suite of plugins (e.g. the
# printer control/watchdog/autoeject trio) can share ONE namespace.
def get_plugin_config(namespace: str) -> dict:
    """All stored values for a namespace (empty dict if none set yet)."""
    cfg = load_api_keys().get("plugin_config")
    val = cfg.get(namespace) if isinstance(cfg, dict) else None
    return dict(val) if isinstance(val, dict) else {}


def get_plugin_setting(namespace: str, key: str, default=None):
    """A single value from a namespace, or `default` if unset."""
    return get_plugin_config(namespace).get(key, default)


def save_plugin_config(namespace: str, values: dict) -> None:
    """Merge `values` into a namespace's stored config. Only the provided keys
    are touched."""
    data = load_api_keys()
    pc = data.get("plugin_config")
    if not isinstance(pc, dict):
        pc = {}
    cur = pc.get(namespace)
    if not isinstance(cur, dict):
        cur = {}
    cur.update(values)
    pc[namespace] = cur
    data["plugin_config"] = pc
    _write(data)


def save_plugin_enabled(plugin_name: str, enabled: bool) -> None:
    data = load_api_keys()
    plugins_cfg = data.get("plugins_enabled")
    if not isinstance(plugins_cfg, dict):
        plugins_cfg = {}
    plugins_cfg[plugin_name] = enabled
    data["plugins_enabled"] = plugins_cfg
    _write(data)


def adopt_legacy_settings(user_id: int) -> None:
    """The first account takes over the names, voice and tutor settings made
    before accounts existed (they stay in api_keys.json as well)."""
    user_file = profile.settings_path(user_id)
    if user_file is None or user_file.exists():
        return
    shared = _read(CONFIG_FILE)
    mine = {k: shared[k] for k in USER_KEYS if k in shared}
    user_file.parent.mkdir(parents=True, exist_ok=True)
    user_file.write_text(json.dumps(mine, indent=4, ensure_ascii=False), encoding="utf-8")
