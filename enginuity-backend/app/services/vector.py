# app/services/vector.py
from typing import List, Dict, Tuple
from pathlib import Path
from app.core.config import get_settings
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# use a local model (no API key required)
_embedder = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

def _client():
    settings = get_settings()
    persist = Path(settings.VECTORDB_DIR).resolve()
    persist.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist))

def collection(name: str = "enginuity") -> chromadb.api.models.Collection.Collection:
    cli = _client()
    try:
        return cli.get_collection(name=name, embedding_function=_embedder)
    except Exception:
        return cli.create_collection(name=name, embedding_function=_embedder)

def index_sections(lecture_title: str, sections: List[Dict]) -> None:
    col = collection()
    ids = [s["id"] for s in sections]
    docs = [s["content"] for s in sections]
    metas = [{"title": lecture_title, "section_id": s["id"]} for s in sections]
    col.upsert(ids=ids, documents=docs, metadatas=metas)

def search(q: str, top_k: int = 5) -> List[Dict]:
    col = collection()
    res = col.query(query_texts=[q], n_results=top_k)
    out: List[Dict] = []
    if not res or not res.get("documents"):
        return out
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res.get("distances", [[ ]])[0] if res.get("distances") else [None]*len(docs)
    for doc, meta, dist in zip(docs, metas, dists):
        out.append({
            "title": "Match",
            "snippet": doc[:280] + ("…" if len(doc) > 280 else ""),
            "score": 1.0 - float(dist) if dist is not None else None,  # convert distance to pseudo-score
            "section_id": meta.get("section_id"),
            "source": meta.get("title", "Notes"),
        })
    return out
