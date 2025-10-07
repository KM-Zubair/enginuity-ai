from fastapi import APIRouter
from app.services.io import read_json, notes_json
from app.models.schemas import NotesDoc

router = APIRouter()

@router.get("", response_model=NotesDoc)
def get_notes():
    sample = {
        "lecture_title": "Sample Notes",
        "generated_at": 0,
        "sections": [
            {"id": "sec-1", "title": "Signals & Systems", "type": "text",
             "content": "Definition, block diagrams, linearity, time-invariance…"},
            {"id": "sec-2", "title": "Laplace Transform", "type": "latex",
             "content": "$$\\mathcal{L}\\{f(t)\\} = \\int_0^\\infty f(t)e^{-st} dt$$"},
            {"id": "sec-3", "title": "Example Code", "type": "code", "language": "python",
             "content": "import numpy as np\nt = np.linspace(0,1,1000)\n"},
        ],
    }
    doc = read_json(notes_json(), sample)
    return doc
