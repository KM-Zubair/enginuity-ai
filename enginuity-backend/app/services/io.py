import json, os
from pathlib import Path
from app.core.config import get_settings

def data_dir() -> Path:
    return Path(get_settings().DATA_DIR).resolve()

def notes_json() -> Path:
    return data_dir() / "notes.json"

def uploads_json() -> Path:
    return data_dir() / "uploads.json"

def read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
