from fastapi import APIRouter
from app.models.schemas import SearchRequest, SearchHit
from typing import List
from app.services.vector import search as vec_search

router = APIRouter()

@router.post("", response_model=List[SearchHit])
def run_search(req: SearchRequest):
    q = req.q.strip()
    if not q:
        return []
    hits = vec_search(q, top_k=req.top_k)
    return [SearchHit(**h) for h in hits]
