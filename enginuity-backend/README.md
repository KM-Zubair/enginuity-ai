# Enginuity Backend (FastAPI)

A minimal FastAPI backend wired to your Streamlit UI.

## Run locally

```bash
cd enginuity-backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health` — service status
- `GET /notes` — returns `data/notes.json` (or sample)
- `POST /search` — demo hybrid search results
- `POST /quiz` — returns MCQ/FIB items (demo set)
- `POST /chat` — RAG-style placeholder response with citations
- `POST /export` — returns a Markdown export (stub)

## Connect from Streamlit

Add something like this where you call the API:

```python
import httpx, os
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

resp = httpx.post(f"{FASTAPI_URL}/search", json={"q": q, "top_k": top_k, "mode": "hybrid"})
hits = resp.json()
```

> Tip: set `FASTAPI_URL` in your Streamlit run env:  
> `FASTAPI_URL=http://localhost:8000 streamlit run Home.py`

## Next steps

- Replace demo logic with real ingestion, chunking, embedding, and retrieval.
- Add SQLAlchemy models for lectures/users/chunks.
- Plug in Chroma/FAISS/Pinecone for embeddings.
- Add auth (optional) and rate limiting for endpoints.
