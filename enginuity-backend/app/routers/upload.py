# app/routers/upload.py
from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from pathlib import Path
from datetime import datetime
from app.core.config import get_settings
from app.services.extract import extract_text
from app.services.chunk import simple_chunk
from app.services.vector import index_sections
from app.services.io import write_json, notes_json

router = APIRouter()

@router.post("")
async def upload(files: List[UploadFile] = File(...), kind: str = Form("doc")):
    """
    1) Save files to DATA_DIR/uploads
    2) Extract text
    3) Chunk -> sections
    4) Save notes.json
    5) Upsert into Chroma
    """
    settings = get_settings()
    data_dir = Path(settings.DATA_DIR).resolve()
    up_dir = data_dir / "uploads"
    up_dir.mkdir(parents=True, exist_ok=True)

    full_texts = []
    lecture_title = None

    for f in files:
        dest = up_dir / f.filename
        dest.write_bytes(await f.read())
        title, txt = extract_text(dest)
        lecture_title = lecture_title or title
        if txt:
            full_texts.append(txt)

    combined = "\n\n".join(full_texts).strip() if full_texts else ""
    if not combined:
        return {"ok": False, "msg": "No text extracted."}

    sections = simple_chunk(combined)

    doc = {
        "lecture_title": lecture_title or "Notes",
        "generated_at": int(datetime.now().timestamp()),
        "sections": sections
    }
    write_json(notes_json(), doc)

    # index vectors for search/chat
    index_sections(doc["lecture_title"], sections)

    return {"ok": True, "lecture_title": doc["lecture_title"], "n_sections": len(sections)}
