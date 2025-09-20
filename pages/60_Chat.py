# chat.py
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
# st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="wide")

load_css("base.css")

# Gate until corpus exists
if not st.session_state.get("has_corpus"):
    st.warning("Upload and process a lecture to chat with your notes.")
    try:
        st.page_link("pages/Upload.py", label="Go to Upload", icon="📤")
    except Exception:
        pass
    st.stop()

st.markdown('<div class="chat-page">', unsafe_allow_html=True)
st.title("AI Assistant")

# ---------- Runtime state ----------
st.session_state.setdefault(
    "messages",
    [{"role": "assistant", "content": "Ask me about your lecture."}]
)
st.session_state.setdefault("chat_meta", {})

# ---------- Controls (context + generation) ----------
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
ctx_mode = c1.selectbox("Context", ["Notes only", "Notes + Web"], index=0)
top_k = c2.slider("Top-k", min_value=3, max_value=10, value=5)
temperature = c3.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
show_citations = c4.toggle("Show citations", value=True)

# Actions row
a1, a2 = st.columns([1, 1])
with a1:
    if st.button("Clear chat 🗑️"):
        st.session_state["messages"] = [{"role": "assistant", "content": "Ask me about your lecture."}]
with a2:
    export_payload = {
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "ctx_mode": ctx_mode,
            "top_k": top_k,
            "temperature": temperature,
        },
        "messages": st.session_state["messages"],
    }
    st.download_button(
        "Export .json",
        data=json.dumps(export_payload, indent=2),
        file_name="chat_export.json"
    )

st.divider()

# ---------- Renderer with optional citations ----------
def render_message(msg):
    role = msg.get("role", "assistant")
    content = msg.get("content", "")
    cites = msg.get("citations", [])  # list of {title, section_id?, score?, snippet?}

    with st.chat_message(role):
        # Support either plain string or dict {"text": "..."}
        if isinstance(content, dict):
            st.markdown(content.get("text", ""))
        else:
            st.markdown(content)

        if show_citations and role == "assistant" and cites:
            with st.expander("Sources"):
                for i, c in enumerate(cites, 1):
                    title = c.get("title", f"Source {i}")
                    sec = c.get("section_id")
                    score = c.get("score")
                    snip = c.get("snippet", "")
                    line = title
                    if sec:
                        line += f" · Section: {sec}"
                    if score is not None:
                        line += f" · Score: {score:.2f}"
                    st.markdown(f"- **{line}**")
                    if snip:
                        st.caption(snip)

# Render chat so far
for m in st.session_state["messages"]:
    render_message(m)

# ---------- Input ----------
prompt = st.chat_input("Type your question…")
if prompt:
    # Append user turn
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ---- Call backend (replace demo with real call) ----
    # Example contract:
    # payload = {
    #   "messages": st.session_state["messages"],
    #   "top_k": top_k,
    #   "temperature": temperature,
    #   "ctx_mode": "notes" if ctx_mode == "Notes only" else "notes+web"
    # }
    # import httpx
    # resp = httpx.post(f"{FASTAPI_URL}/chat", json=payload, timeout=60.0)
    # data = resp.json()  # { "text": "...", "citations": [ {title, section_id?, score?, snippet?}, ... ] }

    # --- Demo answer (placeholder) ---
    demo_text = (
        "Stability requires all poles to lie in the left half-plane. "
        "For a step input, you can examine the dominant pole of the transfer function to estimate settling time."
    )
    demo_citations = [
        {
            "title": "Poles & stability",
            "section_id": "sec-1",
            "score": 0.78,
            "snippet": "A linear system is stable if all poles lie strictly in the left half-plane."
        },
        {
            "title": "Laplace Transform — definition",
            "section_id": "sec-2",
            "score": 0.73,
            "snippet": "𝓛{f(t)} = ∫₀^∞ f(t)e^{-st} dt; use poles of H(s) to analyze stability."
        }
    ]
    answer_msg = {
        "role": "assistant",
        "content": {"text": demo_text},
        "citations": demo_citations
    }

    # Append assistant turn
    st.session_state["messages"].append(answer_msg)
    render_message(answer_msg)

    # Keep chat size reasonable (avoid unbounded growth)
    if len(st.session_state["messages"]) > 60:
        st.session_state["messages"] = st.session_state["messages"][-60:]

st.markdown('</div>', unsafe_allow_html=True)
