# ui/bootstrap.py
from __future__ import annotations
import os
import httpx
import streamlit as st
from typing import Optional, Dict, Any

FASTAPI_URL = (os.getenv("FASTAPI_URL", "http://127.0.0.1:8000") or "").rstrip("/")

def ensure_corpus() -> bool:
    """
    If session has no 'has_corpus', check backend /corpus/status.
    Sets session keys:
      - has_corpus (bool)
      - lecture_title (str|None)
      - generated_at (int|None)
      - sections_count (int)
    Returns True if corpus exists.
    """
    if st.session_state.get("has_corpus") is True:
        return True

    try:
        r = httpx.get(f"{FASTAPI_URL}/corpus/status", timeout=10.0)
        r.raise_for_status()
        meta: Dict[str, Any] = r.json()
        ready = bool(meta.get("ready"))
        st.session_state["has_corpus"] = ready
        st.session_state["lecture_title"] = meta.get("lecture_title")
        st.session_state["generated_at"] = meta.get("generated_at")
        st.session_state["sections_count"] = int(meta.get("sections") or 0)
        return ready
    except Exception:
        # leave as-is; page may still fallback to local sample if available
        return bool(st.session_state.get("has_corpus"))
