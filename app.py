"""Astroman AI - home. Drop-in replacement for the original app.py (back up yours first)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from lib import ui_premium as ui
from lib import icons
from lib import mock

st.set_page_config(page_title="Astroman AI · KP Prashna Kundli", page_icon="✦", layout="wide")
ui.inject()
ui.nav("home")
ui.hero()

# ------------------------------------------------------- trust strip ---
ui.section_head("Why seekers trust us", "Honest astrology, stated plainly",
                "No inflated claims. No fear-selling. Just the method, the maths, and the numbers — published openly.")

st.markdown("<div class='wrap'><div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:18px;margin-top:26px'>",
            unsafe_allow_html=True)
trust = [
    (icons.shield(), "Published accuracy",
     "On 369 published KP textbook cases, our engine agrees with the book's outcome <b>59% of the time</b> — "
     "stated openly instead of claiming 95%. Real-world accuracy is now being measured from user outcomes."),
    (icons.book(), "Primary-source rules",
     "Every engine rule was verified line-by-line against <b>KP Reader VI</b> and the KP Ezine archives. "
     "Nothing is hardcoded on hearsay."),
    (icons.star(), "Free, private, no account",
     "The instant reading is <b>free forever</b>. No signup needed, and your question never leaves the reading. "
     "Outcomes you share are only used to calibrate the engine."),
]
for icon, title, body in trust:
    st.markdown(f"""<div class="pcard reveal">{icon}<h3>{title}</h3>
      <p class="muted" style="line-height:1.7">{body}</p></div>""", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

# ------------------------------------------------------- how it works --
ui.section_head("The method", "How a Prashna reading works",
                "Prashna Kundli — the chart of the <i>question</i>, cast for the exact moment you ask.")

steps = [
    ("01", "Ask one clear question", "Hold it sincerely in mind. One question at a time gives the cleanest chart."),
    ("02", "Choose your cosmic number", "Any number from 1 to 249 — the seed your chart is built from. Or let the cosmos choose."),
    ("03", "Tell us your city", "The chart is cast for your place and this very moment, in IST."),
    ("04", "The engine does the mathematics", "The sub-lord of your question's key house decides. Four steps scored from −8 to +8."),
    ("05", "Receive your answer", "A clear verdict, what the score means, and your supportive timing windows."),
]
st.markdown("<div class='wrap'>", unsafe_allow_html=True)
for n, t, d in steps:
    st.markdown(f"""<div class="pcard reveal" style="display:flex;gap:22px;align-items:flex-start">
      <div class="serif" style="font-size:2rem;color:#c9a227;min-width:64px">{n}</div>
      <div><h3 style="margin:.2rem 0">{t}</h3><p class="muted" style="margin:0;line-height:1.7">{d}</p></div>
      </div>""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------- sample reading -
ui.section_head("See it work", "A sample reading",
                "This is exactly what you receive — verdict, score, chart, and timing. Try it live below.")
st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)
rd = mock.SAMPLE_READING
ui.verdict_card(rd["headline"], rd["story"], rd["kp_score"], rd["score_band"])
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("""<div class="wrap" style="text-align:center;margin-top:26px">
  <p class="muted">Sample data shown. Your real reading is cast fresh for your question.</p></div>""",
            unsafe_allow_html=True)

# ------------------------------------------------------- CTA band -------
st.markdown("""<div style="margin:70px 0 0;padding:70px 24px;text-align:center;
  background:radial-gradient(800px 400px at 50% 0%,#1b2348,#0a0d1a);border-top:1px solid rgba(201,162,39,.25)">
  <div class="eyebrow">Begin</div>
  <h2 class="serif gold-text" style="font-size:2.4rem;margin:.8rem 0">The stars are already moving.</h2>
  <p class="muted" style="max-width:520px;margin:0 auto 28px">One sincere question. One number. Your answer in seconds.</p>
  </div>""", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    st.page_link("pages/1_Astroman_AI.py", label="Ask Your Question")

# ------------------------------------------------------- reviews -------
ui.section_head("Voices", "What seekers say", "Sample reviews — the live wall arrives with Organ 3.")
st.markdown("<div class='wrap'><div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-top:26px'>",
            unsafe_allow_html=True)
for r in mock.SAMPLE_REVIEWS:
    stars = icons.star(16)
    st.markdown(f"""<div class="pcard reveal">{stars * r['stars']}
      <p style="line-height:1.75;font-style:italic">“{r['text']}”</p>
      <div class="muted">— {r['name']}</div></div>""", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)

# ------------------------------------------------------- paid ----------
st.markdown("""<div class="wrap"><div class="pcard reveal" style="text-align:center;margin-top:44px">
  <div class="eyebrow">For life's big decisions</div>
  <h3 class="serif" style="font-size:1.5rem">A human-checked detailed reading</h3>
  <p class="muted" style="max-width:560px;margin:0 auto;line-height:1.7">
  The free AI reading is instant and honest. For the decisions that keep you up at night —
  a detailed personal reading, manually verified, with timing explained in depth.
  <br><b style="color:#f5f0e6">Paid readings open soon.</b></p></div></div>""",
            unsafe_allow_html=True)

ui.footer()
