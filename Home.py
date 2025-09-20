import sys
from pathlib import Path
from textwrap import dedent
import streamlit as st
from ui.theme import load_css

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Enginuity AI", page_icon="⚙️", layout="wide")
# Load CSS directly
css_file = Path("ui/theme/base.css")
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.error("❌ base.css not found")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_css("base.css")

# --- Hero Banner (clean, no demo box) ---
st.markdown(
    dedent("""
    <section class="hero">
      <h1>⚙️ Enginuity AI</h1>
      <p>
        Transform engineering lectures into structured, accessible study notes.  
        Upload audio, slides, or PDFs and get transcripts, formulas, code highlights, quizzes, and an AI chatbot.
      </p>
      <a href="pages/10_Upload.py" target="_self" class="cta-btn">🚀 Get Started</a>
    </section>
    """),
    unsafe_allow_html=True,
)

# --- Features Grid ---
st.markdown(
    dedent("""
    <section class="features">
      <div class="features-grid">
        <div class="card"><div class="icon">📤</div><a href="pages/10_Upload.py">Upload</a></div>
        <div class="card"><div class="icon">📓</div><a href="pages/30_Notes.py">Notes</a></div>
        <div class="card"><div class="icon">🔍</div><a href="pages/40_Search.py">Search</a></div>
        <div class="card"><div class="icon">🧩</div><a href="pages/50_Quiz.py">Quiz</a></div>
        <div class="card"><div class="icon">🤖</div><a href="pages/60_Chat.py">Ask AI</a></div>
        <div class="card"><div class="icon">🧪</div><a href="./?demo=1">Sample Lecture</a></div>
      </div>
    </section>
    """),
    unsafe_allow_html=True,
)