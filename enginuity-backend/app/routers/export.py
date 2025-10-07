from fastapi import APIRouter, HTTPException
from app.models.schemas import ExportRequest
from app.services.io import read_json, notes_json

router = APIRouter()

@router.post("")
def do_export(req: ExportRequest):
    # Minimal stub: return markdown concatenation
    doc = read_json(notes_json(), {"lecture_title": "Notes", "sections": []})
    md = "# " + doc.get("lecture_title", "Notes") + "\n\n" + "\n\n".join(
        [f"## {s.get('title','Untitled')}\n\n{s.get('content','')}" for s in doc.get("sections", [])]
    )
    return {"format": req.format, "content": md}
