"""Reviews - approved seeker testimonials + submission form (Organ 3)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from lib import ui_premium as ui
from lib import icons
from lib import sheets

st.set_page_config(page_title="Reviews · Astroman AI", page_icon="✦", layout="wide")
ui.inject()
ui.nav("reviews")

st.markdown("""<div class="wrap-narrow" style="text-align:center;margin:44px auto 26px">
  <div class="eyebrow">Proof, not promises</div>
  <h1 class="serif gold-text" style="font-size:2.6rem;margin:.6rem 0">Seeker reviews</h1>
  <p class="muted">Real outcomes, shared by real seekers. Reviews appear only after the seeker
  confirmed what actually happened.</p></div>""", unsafe_allow_html=True)

st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)

if not sheets.is_configured():
    st.info("Reviews will appear here once the database is connected. "
            "Meanwhile - get a free reading and come back to share your story!")
else:
    reviews = sheets.get_reviews(limit=30)
    if not reviews:
        st.markdown("<div class='pcard' style='text-align:center'><i>No reviews yet - yours could be the first.</i></div>",
                    unsafe_allow_html=True)
    for r in reviews:
        try:
            rating = max(1, min(5, int(r.get("rating") or 5)))
        except (TypeError, ValueError):
            rating = 5
        st.markdown(f"<div class='pcard reveal' style='margin-bottom:14px'>"
                    f"<div class='gold-text serif' style='font-size:1.05rem'>{'★' * rating}{'☆' * (5 - rating)}</div>"
                    f"<p style='margin:.5rem 0'>\"{r.get('text', '')}\"</p>"
                    f"<div class='muted'>- {r.get('name', 'A seeker')}</div></div>",
                    unsafe_allow_html=True)

st.markdown("---", unsafe_allow_html=True)
st.markdown(f"<h3 class='serif'>{icons.chat(20)} Share your experience</h3>", unsafe_allow_html=True)
st.caption("Did a reading come true - or not? Honest reviews (even negative ones) are welcome. "
           "Reviews are moderated before they appear.")
with st.form("review_form"):
    name = st.text_input("Your name (or nickname)")
    rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5)
    text = st.text_area("Your experience", placeholder="What did you ask, and what actually happened?")
    go = st.form_submit_button("Submit review")
if go:
    if not name.strip() or not text.strip():
        st.warning("Please add your name and a few words about your experience.")
    elif not sheets.is_configured():
        st.error("Reviews can't be saved right now (database not connected).")
    else:
        if sheets.add_review(name, rating, text):
            st.success("Thank you! Your review is awaiting moderation and will appear soon.")
        else:
            st.error("Could not save your review. Please try again later.")

st.markdown("</div>", unsafe_allow_html=True)
ui.footer()
