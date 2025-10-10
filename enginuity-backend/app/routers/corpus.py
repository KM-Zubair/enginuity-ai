# enginuity-backend/app/routers/corpus.py
from __future__ import annotations
from fastapi import APIRouter
from typing import Dict, Any
from pathlib import Path
import json
from app.core.config import get_settings

router = APIRouter()

def _load_notes_meta() -> Dict[str, Any]:
    settings = get_settings()
    notes_path = Path(settings.DATA_DIR).joinpath("notes.json").resolve()
    if notes_path.exists():
        try:
            doc = json.loads(notes_path.read_text(encoding="utf-8"))
            sections = doc.get("sections") or []
            title = doc.get("lecture_title") or "Notes"
            ts = doc.get("generated_at")
            return {
                "ready": bool(sections),
                "lecture_title": title,
                "generated_at": ts,
                "sections": len(sections),
            }
        except Exception:
            pass
    return {"ready": False, "lecture_title": None, "generated_at": None, "sections": 0}

@router.get("/status")
def status() -> Dict[str, Any]:
    """
    Returns whether a corpus/notes already exist on disk/DB.
    Frontend uses this to avoid forcing a re-upload.
    """
    meta = _load_notes_meta()
    return {"ok": True, **meta}
