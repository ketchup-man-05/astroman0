"""Help & FAQ."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from lib import ui_premium as ui

st.set_page_config(page_title="Help · Astroman AI", page_icon="✦", layout="wide")
ui.inject()
ui.nav("help")

st.markdown("""<div class="wrap-narrow" style="text-align:center;margin:44px auto 10px">
  <div class="eyebrow">Guidance</div>
  <h1 class="serif gold-text" style="font-size:2.6rem;margin:.6rem 0">Questions, answered</h1>
  <p class="muted">Everything about how Astroman AI works — plainly stated.</p></div>""",
            unsafe_allow_html=True)

st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)
faqs = [
    ("What is KP Prashna Kundli?",
     "Prashna Kundli is the chart of the <i>question</i>. Instead of your birth chart, we cast a chart for the "
     "exact moment you ask, using a number (1–249) you choose as the seed. KP — Krishnamurti Paddhati — decides "
     "the answer from the <i>sub-lord</i> of the key house of your question. It is a mathematical method, not a mood reading."),
    ("What do I need to ask a question?",
     "Three things: one clear question, your current city, and any number from 1 to 249. No birth date, no birth time, no account."),
    ("What does the KP score mean?",
     "Four mathematical steps are scored and added up. +8 is the strongest possible YES, −8 the strongest NO, "
     "0 is perfectly balanced. Most real charts land between −5 and +5."),
    ("What is the 'deciding planet'?",
     "Every topic has a key house — career is the 10th, marriage the 7th, travel the 12th, and so on. "
     "The planet that is the <i>sub-lord</i> of that house's cusp is the decider of your question."),
    ("Why did I get DELAYED instead of NO?",
     "A retrograde planet is touching your question. In KP a retrograde planet never means a flat refusal — "
     "it means delay, postponement, or success on a second attempt."),
    ("How accurate is it?",
     "On 369 published KP textbook cases, the engine agrees with the book's outcome 59% of the time. "
     "We publish that number openly instead of claiming 95%. Real-world accuracy is being measured from user outcomes right now — "
     "which is why we ask you to tell us what actually happened."),
    ("Is it really free?",
     "Yes — the instant reading is free, forever. Detailed human-checked readings are a separate service for life's big decisions."),
    ("Do I need an account?",
     "No. Accounts are optional — they save your history and let us follow up on whether predictions came true."),
    ("Who built the method?",
     "KP — Krishnamurti Paddhati — was systematised by K.S. Krishnamurti. Our engine's rules were verified "
     "line-by-line against KP Reader VI and the KP Ezine archives before a single reading was served."),
]
for q, a in faqs:
    with st.expander(q):
        st.markdown(a)
st.markdown("</div>", unsafe_allow_html=True)
ui.footer()
