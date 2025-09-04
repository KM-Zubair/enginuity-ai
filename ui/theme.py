from pathlib import Path
import streamlit as st

_ASSETS = Path("assets/styles")

def load_css(*files: str):
    """Inject one or more CSS files (from assets/styles) into the page."""
    css_blob = ""
    for f in files:
        p = _ASSETS / f
        if p.exists():
            css_blob += p.read_text(encoding="utf-8") + "\n"
    if css_blob:
        st.markdown(f"<style>{css_blob}</style>", unsafe_allow_html=True)
