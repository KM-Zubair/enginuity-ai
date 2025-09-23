from pathlib import Path
import streamlit as st

def load_css(file_name: str):
    """Load a CSS file from ui/theme/ and inject into Streamlit app"""
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {css_path}")
