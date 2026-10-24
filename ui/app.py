"""
TruthGuard Streamlit Wrapper
Serves the High-Contrast, Clean Neo-Brutalist Single-Page App
"""

import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

st.set_page_config(
    page_title="TruthGuard | Legal Document Precedence Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Read the HTML application
html_path = BASE_DIR / "ui" / "static" / "index.html"
if html_path.exists():
    with open(html_path, "r", encoding="utf-8") as f:
        app_html = f.read()
    components.html(app_html, height=1300, scrolling=True)
else:
    st.error("UI template not found.")
