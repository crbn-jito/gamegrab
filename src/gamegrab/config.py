from pathlib import Path
import tomli
import os
from typing import Dict

DEFAULT = {
    "download_dir": str(Path.home() / "Downloads" / "gamegrab"),
    "concurrency": 3,
    "user_agent": "gamegrab/0.1 (+https://example.org)",
    "retries": 5,
    "timeout_seconds": 30
}

def config_path() -> Path:
    p = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gamegrab" / "config.toml"
    return p

def ensure_config() -> Dict:
    p = config_path()
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("")  # keep empty, loader will apply defaults
    return load_config()

def load_config() -> Dict:
    p = config_path()
    if not p.exists():
        return DEFAULT.copy()
    try:
        data = tomli.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT.copy()
    out = DEFAULT.copy()
    out.update(data or {})
    return out
