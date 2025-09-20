# search.py
import sys
from pathlib import Path
import re
import json
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.theme import load_css

# IMPORTANT: set_page_config should be called only once in the main entry page.
# st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")

load_css("base.css")

if not st.session_state.get("has_corpus"):
    st.warning("Upload and process a lecture to search.")
    try:
        st.page_link("pages/Upload.py", label="Go to Upload", icon="📤")
    except Exception:
        pass
    st.stop()

st.markdown('<div class="search-page">', unsafe_allow_html=True)
st.title("Search Notes")

# Optional: read metadata to display context
DATA_DIR = Path("data")
NOTES_JSON = DATA_DIR / "notes.json"
lecture_title = "Notes"
if NOTES_JSON.exists():
    try:
        notes_doc = json.loads(NOTES_JSON.read_text(encoding="utf-8"))
        lecture_title = notes_doc.get("lecture_title", lecture_title)
        ts = notes_doc.get("generated_at")
        if ts:
            st.caption(f"Lecture: **{lecture_title}** · Generated: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')}")
    except Exception:
        st.caption(f"Lecture: **{lecture_title}**")

# --- Search controls (use a form so Enter submits) ---
with st.form("search_form", clear_on_submit=False):
    q = st.text_input("Enter search query", placeholder="e.g., Laplace stability condition")
    colA, colB, colC = st.columns([1, 1, 1])
    top_k = colA.slider("Results", 3, 15, 5)
    mode = colB.selectbox("Mode", ["Hybrid", "Keyword", "Semantic"])
    show_snippets = colC.toggle("Show snippets", value=True)
    submitted = st.form_submit_button("Search", use_container_width=False)

# Map UI mode to backend param
mode_map = {"Hybrid": "hybrid", "Keyword": "keyword", "Semantic": "semantic"}

# --- Run search ---
if submitted:
    q_clean = q.strip()
    if not q_clean:
        st.warning("Please enter a query.")
    else:
        # TODO: Replace with real backend call, e.g.:
        # import httpx
        # resp = httpx.post(f"{FASTAPI_URL}/search", json={"q": q_clean, "top_k": top_k, "mode": mode_map[mode]}, timeout=30.0)
        # hits = resp.json()["results"]

        # Demo hits (placeholder)
        demo = [
            {
                "title": "Laplace Transform — definition",
                "snippet": "The Laplace transform of f(t) is defined as 𝓛{f(t)} = ∫₀^∞ f(t)e^{-st} dt.",
                "score": 0.82,
                "section_id": "sec-2",
                "source": lecture_title,
            },
            {
                "title": "Poles & stability",
                "snippet": "A linear system is stable if all poles lie strictly in the left half-plane.",
                "score": 0.77,
                "section_id": "sec-1",
                "source": lecture_title,
            },
        ]
        st.session_state["search_hits"] = demo

# --- Render results ---
hits = st.session_state.get("search_hits", [])

def highlight(text: str, query: str) -> str:
    if not query or not text:
        return text or ""
    # rudimentary highlighter (case-insensitive)
    try:
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", text)
    except re.error:
        return text

if hits:
    st.subheader("Results")
    for i, h in enumerate(hits, 1):
        title = h.get("title", "Untitled")
        snippet = h.get("snippet", "")
        score = float(h.get("score", 0.0))
        section_id = h.get("section_id")
        source = h.get("source", lecture_title)

        # Build a small card with a score pill and optional snippet
        st.markdown(
            f"""
            <div class="result-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <h4 style="margin:0;">{i}. {title}</h4>
                <span class="score">{score:.2f}</span>
              </div>
              <div class="meta">Source: {source}{f" · Section: {section_id}" if section_id else ""}</div>
              {"<p>"+ highlight(snippet, q) +"</p>" if show_snippets and snippet else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Actions row
        a1, a2, a3 = st.columns([1, 1, 6])
        with a1:
            # Open in Notes (can’t deep-link anchors reliably; cue the user)
            st.button("Open in Notes", key=f"open-{i}")
        with a2:
            st.button("Copy citation", key=f"cite-{i}")
        # (You can wire Open in Notes to set a session var like st.session_state['notes_focus']=section_id)

else:
    st.info("Type a query and press **Search** to see results.")
    st.caption("Tips: try concept names (\"Laplace\"), code terms (\"numpy linspace\"), or questions (\"how to check stability\").")

st.markdown('</div>', unsafe_allow_html=True)
