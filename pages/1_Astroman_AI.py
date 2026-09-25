"""Astroman AI - the reading room. Live engine + narrator + sheets + login + paid tier."""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from lib import ui_premium as ui
from lib import icons
from lib import topics, narrator, sheets, auth, engine_live
from lib.chart_svg import north_indian_svg

st.set_page_config(page_title="Ask · Astroman AI", page_icon="✦", layout="wide")
ui.inject()
ui.nav("ask")

APP_URL = "https://astroman-ai.streamlit.app"

st.markdown("""<div class="wrap-narrow" style="text-align:center;margin:44px auto 10px">
  <div class="eyebrow">The reading room</div>
  <h1 class="serif gold-text" style="font-size:2.6rem;margin:.6rem 0">Ask your question</h1>
  <p class="muted">One sincere question. The chart is cast for this very moment.</p></div>""",
            unsafe_allow_html=True)

st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)

# ---------------- account (optional) ----------------
with st.expander("My account (optional) - save your readings", expanded=False):
    user = auth.login_box()
    auth.user_badge()
username = ((auth.current_user() or {}).get("username"))

if username and sheets.is_configured():
    pending = sheets.pending_outcomes(username)
    if pending:
        st.warning(f"You have **{len(pending)}** reading(s) awaiting their outcome. "
                   "Your answers calibrate the engine - please update them below in My Readings.")

# ---------------- cosmic weather ----------------
tithi, weekday, datestr = engine_live.cosmic_weather()
if tithi:
    st.markdown(f"<div class='pcard' style='text-align:center'>{icons.moon(16)} {tithi} &nbsp;|&nbsp; "
                f"{weekday}, {datestr} (IST)</div>", unsafe_allow_html=True)

# ---------------- question form ----------------
question = st.text_input("Your question", placeholder="e.g. Will I get this job?",
                         value=st.session_state.get("preset_q", ""))
st.markdown("<div style='display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 18px'>", unsafe_allow_html=True)
presets = ["Will I get a promotion this year?", "Will my visa be approved?",
           "Should I buy this property?", "Will I clear my exam?"]
for i, p in enumerate(presets):
    if st.button(p, key=f"preset_{i}", type="secondary"):
        st.session_state["preset_q"] = p
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

city = st.text_input("Your current city", value="Shimla")

st.markdown(f"<h3 class='serif' style='margin-top:26px'>{icons.dice(20)} Your cosmic number <span class='muted' style='font-size:.9rem'>(1-249)</span></h3>",
            unsafe_allow_html=True)
st.caption("In KP Prashna this number is the seed of your question. Close your eyes, think of your question - then choose.")
ncol1, ncol2 = st.columns([1, 2])
with ncol1:
    if st.button("Let the cosmos choose", key="cosmos_btn", type="secondary"):
        _n = random.randint(1, 249)
        st.session_state["cosmic_n"] = _n
        st.session_state["cosmic_num"] = _n
with ncol2:
    horary_number = st.number_input("Number", min_value=1, max_value=249,
                                    value=st.session_state.get("cosmic_n", 45),
                                    step=1, key="cosmic_num", label_visibility="collapsed")

topic_label = st.selectbox("Topic", list(topics.TOPIC_OPTIONS.keys()))

if st.button("Cast Horary Chart", type="primary"):
    if not question.strip():
        st.warning("Please write your question first - the stars need something to answer.")
        st.stop()
    with st.spinner("Casting your chart..."):
        reading, err = engine_live.cast(question.strip(), city.strip() or "Shimla",
                                        int(horary_number), topic_label)
    if err:
        st.error(err)
        st.stop()
    st.session_state["reading"] = reading
    if sheets.is_configured():
        rid = sheets.new_reading_id(int(horary_number))
        st.session_state["reading"]["reading_id"] = rid
        sheets.log_reading(rid, username or "anon", question.strip(),
                           reading["topic"], reading["city"], int(horary_number),
                           reading["result"].get("verdict"),
                           reading["result"].get("kp_score"))
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------- reading --
rd = st.session_state.get("reading")
if rd:
    r = rd["result"]
    af = r.get("ai_facts", {})
    verdict, kp_score = r.get("verdict", ""), r.get("kp_score")
    decision = af.get("decision", {})
    headline, story, notes = narrator.verdict_story(verdict, kp_score, decision)

    st.markdown(f"""<div class="wrap-narrow" style="text-align:center;margin-bottom:6px">
      <div class="muted">"{rd['question']}" · {rd['city']} · number {rd['number']}</div></div>""",
                unsafe_allow_html=True)
    ui.verdict_card(headline, story, kp_score, narrator.score_band_text(kp_score))

    st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)
    for n in notes:
        st.info(n)
    sec = (af.get("secondary_signals") or {})
    if sec.get("eleventh_csl_fulfillment"):
        st.caption("11th house confirmation: " + sec["eleventh_csl_fulfillment"])
    if sec.get("moon_genuineness"):
        st.caption("Moon genuineness: " + sec["moon_genuineness"])

    with st.expander("The mathematics - 4 steps, scored"):
        st.caption(narrator.score_legend_md())
        for step in (af.get("step_breakdown") or []):
            if isinstance(step, dict):
                hrs = step.get("house_results") or []
                def _pts(p):
                    return f"{p:+d}" if isinstance(p, (int, float)) else "n/a"
                hr_txt = "; ".join(f"house {h.get('house')}: {h.get('classification')} ({_pts(h.get('points'))})"
                                   for h in hrs if isinstance(h, dict))
                st.markdown(f"- **Step {step.get('step')}: {step.get('name')}** - {step.get('planet')}"
                            + (f" - {hr_txt}" if hr_txt else ""))
            else:
                st.markdown(f"- {step}")
        st.markdown(f"- **Key house**: {decision.get('key_house')}th house · "
                    f"**Deciding planet** (cusp sub-lord): **{decision.get('deciding_planet')}** · "
                    f"Star lord: **{decision.get('deciding_planet_star_lord')}**")
        if decision.get("note"):
            st.caption(decision["note"])
        rp = af.get("ruling_planet_check") or {}
        if rp.get("text"):
            st.caption(rp["text"])

    st.markdown("<h3 class='serif'>North Indian chart</h3>", unsafe_allow_html=True)
    try:
        cd = r.get("chart_data", {}) or {}
        svg = north_indian_svg(r.get("horary_ascendant_longitude", 0) or 0, cd.get("planets", {}))
        st.markdown(f"<div style='max-width:420px;margin:0 auto'>{svg}</div>", unsafe_allow_html=True)
    except Exception:
        st.caption("Chart image unavailable for this reading.")

    tstory = narrator.timing_story(af.get("timing"))
    if tstory:
        st.markdown("<h3 class='serif' style='margin-top:28px'>Timing windows</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='pcard reveal'>{tstory}</div>", unsafe_allow_html=True)
    trstory = narrator.transit_story(af.get("transit_confirmation"))
    if trstory:
        st.info(trstory)

    b1, b2 = st.columns(2)
    with b1:
        txt = (f"Astroman AI - KP Horary Reading\n{rd['cast_at']}\n\n"
               f"Question: {rd['question']}\nCity: {rd['city']} | Cosmic number: {rd['number']}\n\n"
               f"Verdict: {verdict}\n{narrator.score_band_text(kp_score)}\n\n{story}\n")
        if tstory:
            txt += f"\nTiming: {tstory}\n"
        st.download_button("Download reading", txt, file_name="astroman_reading.txt")
    with b2:
        wa = "https://wa.me/?text=" + narrator.share_text(
            rd["question"], verdict, kp_score or 0, APP_URL).replace(" ", "%20").replace("\n", "%0A")
        st.link_button("Share on WhatsApp", wa)

    st.markdown("---")
    st.markdown("<h3 class='serif'>Did it come true?</h3>", unsafe_allow_html=True)
    st.caption(narrator.outcome_prompt())
    rid = rd.get("reading_id")
    oc = st.columns(3)

    def _mark(outcome, label, key):
        if oc[{"YES": 0, "NO": 1, "PARTIAL": 2}[outcome]].button(label, key=key, type="secondary"):
            ok = sheets.set_outcome(rid, outcome) if (rid and sheets.is_configured()) else False
            st.session_state["reading"]["outcome"] = outcome
            st.success("Thank you! Your answer makes every future reading sharper."
                       + ("" if ok or not sheets.is_configured() else " (saved locally for now)"))

    _mark("YES", "It came true", f"out_{rid}_YES")
    _mark("NO", "It didn't", f"out_{rid}_NO")
    _mark("PARTIAL", "Partly / not yet", f"out_{rid}_PARTIAL")

    st.markdown("<h3 class='serif' style='margin-top:26px'>Instant answers</h3>", unsafe_allow_html=True)
    f = st.columns(3)
    if f[0].button("When will it happen?", key="fq_when", type="secondary"):
        st.info(tstory or "No clear timing window appeared in this chart - patience is the strategy.")
    if f[1].button("Why this answer?", key="fq_why", type="secondary"):
        st.info(f"The deciding planet is the sub-lord of your question's key house cusp. "
                f"Its 4-step score came to {kp_score:+d}. " + story)
    if f[2].button("What should I do?", key="fq_what", type="secondary"):
        st.info("For the decisions that matter most, a human-checked detailed reading goes deeper - see below.")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------- history --
st.markdown("<div class='wrap-narrow'>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"<h3 class='serif'>{icons.clock(20)} My readings</h3>", unsafe_allow_html=True)
if username and sheets.is_configured():
    rows = sheets.get_user_readings(username)
    if not rows:
        st.caption("No saved readings yet - cast your first one above!")
    for row in rows[:10]:
        ocv = row.get("outcome")
        badge = {"YES": "Came true", "NO": "Did not", "PARTIAL": "Partly / not yet"}.get(ocv, "Awaiting outcome")
        with st.expander(f"{(row.get('question') or '')[:60]} - {(row.get('verdict') or '')[:40]} · {badge}"):
            st.caption(f"{(row.get('created_at_utc') or '')[:16]} UTC · {row.get('city')} · number {row.get('horary_number')}")
            if not ocv:
                bc = st.columns(3)
                if bc[0].button("Came true", key=f"h_yes_{row['reading_id']}", type="secondary"):
                    sheets.set_outcome(row["reading_id"], "YES"); st.rerun()
                if bc[1].button("Did not", key=f"h_no_{row['reading_id']}", type="secondary"):
                    sheets.set_outcome(row["reading_id"], "NO"); st.rerun()
                if bc[2].button("Not yet", key=f"h_part_{row['reading_id']}", type="secondary"):
                    sheets.set_outcome(row["reading_id"], "PARTIAL"); st.rerun()
else:
    st.caption("Log in above to keep your readings here across visits.")
st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------- paid tier --
def _paid_card():
    try:
        number = st.secrets.get("whatsapp_number", "")
    except Exception:
        number = ""
    st.markdown("<div class='wrap-narrow'><div class='pcard reveal' style='text-align:center'>", unsafe_allow_html=True)
    st.markdown("<h3 class='serif'>Want a human-checked detailed reading?</h3>", unsafe_allow_html=True)
    st.markdown("<p class='muted'>The free reading above is instant. For the decisions that matter most, "
                "get a detailed personal reading - manually verified, with remedies and timing explained.</p>",
                unsafe_allow_html=True)
    if number:
        url = ("https://wa.me/" + str(number) + "?text="
               + "Hi! I want a detailed personal KP reading.".replace(" ", "%20"))
        st.link_button("Chat on WhatsApp", url, type="primary")
    else:
        st.caption("Paid readings opening soon - meanwhile the free readings are unlimited.")
    st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
_paid_card()

ui.footer()
