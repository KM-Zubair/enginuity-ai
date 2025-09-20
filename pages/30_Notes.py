# notes.py
import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from ui.theme import load_css

# IMPORTANT: set_page_config should be called only once in the main entry page.
# st.set_page_config(page_title="Notes", page_icon="📓", layout="wide")

load_css("base.css")

if not st.session_state.get("has_corpus"):
    st.warning("Upload and process a lecture to view notes.")
    # Adjust the path/label below to match your actual Upload page
    try:
        st.page_link("pages/Upload.py", label="Go to Upload", icon="📤")
    except Exception:
        pass
    st.stop()

st.markdown('<div class="notes-page">', unsafe_allow_html=True)
st.title("Lecture Notes")

DATA_DIR = Path("data")
NOTES_JSON = DATA_DIR / "notes.json"  # backend should write this after indexing
META_JSON = DATA_DIR / "uploads.json"  # optional: to show context/source

def load_notes():
    """
    Expected schema (example):
    {
      "lecture_title": "Signals & Systems - Lecture 3",
      "generated_at": 1726789123,
      "sections": [
        {"id": "sec-1", "title": "Signals & Systems", "type": "text", "content": "Definition…"},
        {"id": "sec-2", "title": "Laplace Transform", "type": "latex", "content": "\\\\mathcal{L}\\{f(t)\\}=…"},
        {"id": "sec-3", "title": "Example Code", "type": "code", "language": "python", "content": "import numpy as np\\n..."}
      ]
    }
    """
    if NOTES_JSON.exists():
        try:
            return json.loads(NOTES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Fallback to your placeholder content
    return {
        "lecture_title": "Sample Notes",
        "generated_at": int(datetime.now().timestamp()),
        "sections": [
            {"id": "sec-1", "title": "Signals & Systems", "type": "text",
             "content": "Definition, block diagrams, linearity, time-invariance…"},
            {"id": "sec-2", "title": "Laplace Transform", "type": "latex",
             "content": r"$$\mathcal{L}\{f(t)\} = \int_0^\infty f(t)e^{-st} dt$$"},
            {"id": "sec-3", "title": "Example Code", "type": "code", "language": "python",
             "content": "import numpy as np\nt = np.linspace(0,1,1000)\n"},
        ],
    }

notes = load_notes()
sections = notes.get("sections", [])
lecture_title = notes.get("lecture_title", "Untitled")
generated_at = notes.get("generated_at")

# Header metadata
cols = st.columns([3, 2, 1])
with cols[0]:
    st.caption(f"Lecture: **{lecture_title}**")
with cols[1]:
    if generated_at:
        ts = datetime.fromtimestamp(generated_at).strftime("%Y-%m-%d %H:%M")
        st.caption(f"Generated: **{ts}**")
with cols[2]:
    # Download full markdown export (simple join for now)
    md_export = "# " + lecture_title + "\n\n" + "\n\n".join(
        [f"## {s['title']}\n\n{s['content']}" for s in sections]
    )
    st.download_button("Download .md", data=md_export, file_name="lecture-notes.md")

left, right = st.columns([1, 3], gap="large")

with left:
    st.markdown('<div class="sticky-left">', unsafe_allow_html=True)

    st.subheader("Contents")

    # Search filter
    q = st.text_input("Search", placeholder="Filter sections…").strip().lower()
    filtered = [
        s for s in sections
        if (q in s["title"].lower() or q in s.get("content", "").lower())
    ] if q else sections

    # Radio to select section (anchors don't scroll in Streamlit)
    if filtered:
        selected_title = st.radio(
            "Sections",
            options=[s["title"] for s in filtered],
            label_visibility="collapsed",
            index=0
        )
        # Map back to section id
        selected = next(s for s in filtered if s["title"] == selected_title)
    else:
        st.info("No sections match your search.")
        selected = None

    st.markdown('</div>', unsafe_allow_html=True)


with right:
    if selected:
        st.markdown(f"### {selected['title']}")

        s_type = selected.get("type", "text")
        content = selected.get("content", "")

        if s_type == "code":
            lang = selected.get("language", None)
            # st.code renders with a built-in copy button (fixes your Copy button)
            st.code(content, language=lang)
        elif s_type == "latex":
            st.markdown(content)
        else:
            st.markdown(content)

        # Actions row
        a1, a2, _ = st.columns([1, 1, 6])
        with a1:
            # TTS placeholder: wire this to your backend later
            if st.button("🔊 Read aloud"):
                # TODO: replace with requests.post(...) to /tts then st.audio(bytes_or_url)
                st.info("TTS will be available once connected to the backend.")
        with a2:
            # Per-section download
            st.download_button(
                "⬇️ Save section",
                data=content if s_type != "code" else f"```{selected.get('language','')}\n{content}\n```",
                file_name=f"{selected['title'].replace(' ','_')}.md"
            )

st.markdown('</div>', unsafe_allow_html=True)
