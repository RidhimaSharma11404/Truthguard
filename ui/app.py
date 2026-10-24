"""
TruthGuard Streamlit Wrapper
Serves the High-Contrast, Clean Neo-Brutalist Single-Page App
Exact match to user's desired design language (Centered card, floating assistant, pastel grid)
"""

import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Add truthguard to path
BASE_DIR = Path("C:/Users/Lenovo/.gemini/antigravity/scratch/truthguard")
sys.path.insert(0, str(BASE_DIR))

st.set_page_config(
    page_title="TruthGuard | Legal Document Precedence Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit header, footer, and menu to give a clean native app feel
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    iframe {
        border: none !important;
        width: 100% !important;
        min-height: 100vh !important;
    }
</style>
""", unsafe_allow_html=True)

# Read the HTML application
html_path = BASE_DIR / "ui/static/index.html"
with open(html_path, "r", encoding="utf-8") as f:
    app_html = f.read()

# Render HTML with full interactivity
components.html(app_html, height=1100, scrolling=True)
