# --- ensure top-level packages are importable ---
import sys
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ------------------------------------------------

import streamlit as st
from ui.theme import load_css

st.set_page_config(page_title="Enginuity AI", page_icon="🛠️", layout="wide")
load_css("base.css")  # hero + features-grid styles live here

# --- hero banner ---
st.markdown(
    dedent("""
    <div class="hero">
      <h1 style="margin:0">Enginuity AI</h1>
      <p>Turn engineering lectures into structured, accessible notes.</p>
    </div>
    """),
    unsafe_allow_html=True,
)

# --- state & query param hook (for the sample tile) ---
st.session_state.setdefault("has_corpus", False)
st.session_state.setdefault("demo_mode", False)

# If user clicked the sample tile (?demo=1), enable features then clear the param
qp = st.query_params
if "demo" in qp:
    st.session_state["has_corpus"] = True
    st.session_state["demo_mode"] = True
    st.success("Sample loaded. Notes/Search/Quiz/Chat enabled.")
    # clear the param so refreshes don't retrigger
    st.query_params.clear()

enabled = st.session_state["has_corpus"]

# --- feature tile HTML helper (left-aligned icon + label) ---
def feature_html(label: str, href: str | None, icon: str, enabled_flag: bool,
                 tooltip: str = "Upload & process a lecture first") -> str:
    if enabled_flag and href:
        return f"""
<div class="feature-item">
  <div class="icon">{icon}</div>
  <a class="label" href="{href}" target="_self">{label}</a>
</div>"""
    else:
        return f"""
<div class="feature-item disabled" title="{tooltip}">
  <div class="icon">{icon}</div>
  <div class="eng-muted">{label}</div>
</div>"""

# --- render 2x3 grid (sample tile is real link via ?demo=1) ---
grid_html = f"""
<div class="features-grid">
  {feature_html("Upload", "pages/10_Upload.py", "📤", True)}
  {feature_html("Notes",  "pages/30_Notes.py",  "📓", enabled)}
  {feature_html("Search", "pages/40_Search.py", "🔍", enabled)}
  {feature_html("Quiz",   "pages/50_Quiz.py",   "🧩", enabled)}
  {feature_html("Ask AI",   "pages/60_Chat.py",   "🤖", enabled)}
  <div class="feature-item">
    <div class="icon">🧪</div>
    <a class="label" href="./?demo=1" target="_self">Load sample lecture</a>
  </div>
</div>
"""

st.markdown(dedent(grid_html), unsafe_allow_html=True)
