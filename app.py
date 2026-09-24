import transit_engine
import streamlit as st
import urllib.parse
import uuid
from typing import Any
import html

import chart_caster

# ----------------------------------------------------------------------
# 2. Session State Initialization Wrapper
# ----------------------------------------------------------------------
def _ensure(key: str, default: Any) -> Any:
    """Return existing session_state[key] or set it to default safely."""
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

def init_session_state():
    _ensure("session_id", str(uuid.uuid4()))
    _ensure("user_sessions", {})
    _ensure("chat_history", [])
    _ensure("reading_done", False)
    _ensure("question_input", "")
    _ensure("user_city", "Shimla")
    _ensure("cosmic_number", 45)
    _ensure("raw_planets", None)
    _ensure("raw_ascendant", None)
    _ensure("raw_planet_houses", None)
    _ensure("raw_cusps", None)
    _ensure("reading_result", "")

# ----------------------------------------------------------------------
# 3. Cached Functions & UI Helpers
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def _load_live_weather(lon: float = 77.17) -> str:
    """Cache the live weather. 'lon' defaults to Shimla's longitude."""
    day_name, day_lord = chart_caster.get_current_day_lord(lon)
    planets, _ = transit_engine.get_live_planets()
    tithi = chart_caster.get_panchang_tithi(planets["Sun"], planets["Moon"])
    return f"🌙 {tithi} | ☀️ Day of {day_name} ({day_lord})"

def extract_chart_render_state(session_data):
    """Pull chart render data from a stored engine payload."""
    reading_data = session_data.get("chart_data", {})
    chart_metadata = reading_data.get("chart_data", {})
    if not chart_metadata:
        return {"raw_planets": None, "raw_ascendant": None, "raw_planet_houses": None, "raw_cusps": None}

    return {
        "raw_planets": chart_metadata.get("planets"),
        "raw_ascendant": reading_data.get("horary_ascendant_longitude"),
        "raw_planet_houses": chart_metadata.get("planet_houses"),
        "raw_cusps": chart_metadata.get("cusps")
    }

def draw_north_indian_chart(planets_dict, ascendant_lon):
    """
    Renders a standard North Indian Rasi (Whole Sign) chart.
    Numbers represent the Zodiac Sign (1-12). Planets are placed in the box of their sign.
    Styled to match the Streamlit Dark Mode UI.
    """
    if ascendant_lon is None: return ""

    ABBR = {
        "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
        "Rahu": "Ra", "Ketu": "Ke"
    }

    # Calculate Ascendant Sign (1-12)
    asc_sign = int((ascendant_lon % 360) // 30) + 1

    house_planets = {h: [] for h in range(1, 13)}
    house_planets[1].append("La")

    # Place planets strictly by their Sign (Whole Sign logic)
    for p, lon in planets_dict.items():
        p_sign = int((lon % 360) // 30) + 1
        box_idx = (p_sign - asc_sign) % 12 + 1
        short_name = ABBR.get(p, p[:2])
        house_planets[box_idx].append(short_name)

    def get_sign_num(h):
        return (asc_sign + h - 2) % 12 + 1

    p_txt = {h: " ".join(house_planets[h]) for h in range(1, 13)}
    s_num = {h: str(get_sign_num(h)) for h in range(1, 13)}

    # UI Matching Colors
    bg = "#1E293B"       # Slate background
    lines = "#475569"    # Slate borders
    p_col = "#E2E8F0"    # White text for planets
    s_col = "#60A5FA"    # Blue text for numbers

    # Single-line HTML string to ensure native st.markdown renders it perfectly without iframe clipping
    svg = f"""<div style="display: flex; justify-content: center; margin: 15px 0 25px 0;"><svg viewBox="0 0 400 400" width="100%" style="max-width: 420px; background-color: {bg}; border: 2px solid {lines}; border-radius: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;"><rect x="0" y="0" width="400" height="400" fill="none" stroke="{lines}" stroke-width="2"/><line x1="0" y1="0" x2="400" y2="400" stroke="{lines}" stroke-width="1.8"/><line x1="400" y1="0" x2="0" y2="400" stroke="{lines}" stroke-width="1.8"/><polygon points="200,0 400,200 200,400 0,200" fill="none" stroke="{lines}" stroke-width="1.8"/><text x="200" y="85" text-anchor="middle" font-size="14" font-weight="700" fill="{p_col}">{p_txt[1]}</text><text x="200" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[1]}</text><text x="80" y="45" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[2]}</text><text x="145" y="45" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[2]}</text><text x="45" y="80" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[3]}</text><text x="45" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[3]}</text><text x="75" y="205" text-anchor="middle" font-size="14" font-weight="700" fill="{p_col}">{p_txt[4]}</text><text x="145" y="205" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[4]}</text><text x="45" y="325" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[5]}</text><text x="45" y="265" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[5]}</text><text x="80" y="360" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[6]}</text><text x="145" y="360" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[6]}</text><text x="200" y="325" text-anchor="middle" font-size="14" font-weight="700" fill="{p_col}">{p_txt[7]}</text><text x="200" y="265" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[7]}</text><text x="320" y="360" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[8]}</text><text x="255" y="360" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[8]}</text><text x="355" y="325" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[9]}</text><text x="355" y="265" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[9]}</text><text x="325" y="205" text-anchor="middle" font-size="14" font-weight="700" fill="{p_col}">{p_txt[10]}</text><text x="255" y="205" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[10]}</text><text x="355" y="80" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[11]}</text><text x="355" y="145" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[11]}</text><text x="320" y="45" text-anchor="middle" font-size="13" font-weight="700" fill="{p_col}">{p_txt[12]}</text><text x="255" y="45" text-anchor="middle" font-size="13" font-weight="700" fill="{s_col}">{s_num[12]}</text></svg></div>"""
    return svg

def main():
    import ai_narrator

    # ------------------------------------------------------------------
    # 1. Page Configuration & CSS
    # ------------------------------------------------------------------
    st.set_page_config(page_title="Astroman AI - KP Horary", page_icon="✨", layout="centered")

    st.markdown("""
    <style>
        .stApp { background-color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, div[data-testid="stMarkdownContainer"] p { color: #F8FAFC !important; }
        header {visibility: hidden;}
        .stTextInput input, .stNumberInput input {
            border-radius: 12px !important; border: 1px solid #334155 !important;
            background-color: #1E293B !important; color: #F8FAFC !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        .stButton > button, .stDownloadButton > button {
            background-color: #3B82F6 !important; color: white !important;
            border-radius: 20px !important; border: 1px solid #60A5FA !important;
            font-weight: 600 !important; padding: 8px 24px !important;
            transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background-color: #2563EB !important; box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5) !important; transform: translateY(-1px);
        }
        .stAlert { background-color: #1E293B !important; border: 1px solid #334155 !important; color: #F8FAFC !important; }
    </style>
    """, unsafe_allow_html=True)
    init_session_state()

    st.title("✨ Astroman AI: KP Horary")

    try:
        weather_info = _load_live_weather()
        st.info(f"**Live Cosmic Weather (Shimla):** {weather_info}")
    except Exception as e:
        st.warning(f"Cosmic Weather sync delayed. (System note: {e})")

    st.markdown("##### What is on your mind? (Quick Select)")
    c1, c2, c3, c4 = st.columns(4)

    def set_question(q: str):
        st.session_state.question_input = q

    if c1.button("💼 Career"): set_question("Will I secure the job after yesterday's interview?")
    if c2.button("❤️ Love"): set_question("Will my current relationship lead to marriage?")
    if c3.button("💰 Wealth"): set_question("Will my upcoming business deal be profitable?")
    if c4.button("📚 Exams"): set_question("Will I pass my upcoming competitive exam?")

    with st.form("astrology_form"):
        question = st.text_input("Your Question", value=st.session_state.question_input, placeholder="e.g. Will I get this job?")
        city = st.text_input("Your Current City", value=st.session_state.user_city)

        horary_number = st.number_input(
            "Your Cosmic Number (1 to 249)",
            min_value=1, max_value=249, value=st.session_state.cosmic_number, step=1,
            help="Close your eyes, focus deeply on your question, and type the very first number between 1 and 249."
        )

        topic_label = st.selectbox(
            "Topic of your question",
            list(ai_narrator.TOPIC_OPTIONS.keys()),
            help="Leave on Auto-detect and the app reads your question. Pick a topic yourself if your question is unusual, so the correct houses are used."
        )

        submitted = st.form_submit_button("Cast Horary Chart & Analyze")

    if submitted:
        if not question or not city:
            st.error("Please fill in both your question and city.")
        else:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.reading_done = False
            st.session_state.question_input = question
            st.session_state.user_city = city
            st.session_state.cosmic_number = horary_number
            st.session_state.chat_history = []

            with st.status("🌌 Consulting the Stars...", expanded=True) as status:
                st.write("Aligning Swiss Ephemeris data...")
                st.write("Locating Placidus Cusps & Ruling Planets...")
                st.write("Consulting Groq 120B AI...")

                try:
                    reply = ai_narrator.handle_incoming_message(
                        st.session_state.session_id,
                        question,
                        city,
                        int(horary_number),
                        topic=ai_narrator.TOPIC_OPTIONS[topic_label]
                    )

                    session_data = st.session_state.user_sessions.get(st.session_state.session_id, {})
                    render_state = extract_chart_render_state(session_data)
                    st.session_state.raw_planets = render_state["raw_planets"]
                    st.session_state.raw_ascendant = render_state["raw_ascendant"]
                    st.session_state.raw_planet_houses = render_state["raw_planet_houses"]
                    st.session_state.raw_cusps = render_state["raw_cusps"]

                    st.session_state.reading_result = reply
                    st.session_state.reading_done = True
                    status.update(label="Cosmic Alignment Complete!", state="complete", expanded=False)

                except Exception as e:
                    status.update(label="Disturbance in the cosmos", state="error")
                    st.error(f"Error calculating reading: {e}")

    if st.session_state.reading_done:
        st.markdown("---")
        st.markdown("### 📜 Your Cosmic Reading")

        if st.session_state.raw_planets and st.session_state.raw_ascendant is not None:
            st.markdown("##### North Indian Chart (Whole Sign)")
            try:
                chart_html = draw_north_indian_chart(
                    st.session_state.raw_planets,
                    st.session_state.raw_ascendant
                )
                st.markdown(chart_html, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to render chart visual. Error: {e}")

        st.write(st.session_state.reading_result)
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            export_text = f"Astroman AI KP Reading\n\nQuestion: {st.session_state.question_input}\nCity: {st.session_state.user_city}\nCosmic Number: {st.session_state.cosmic_number}\n\nResult:\n{st.session_state.reading_result}"
            st.download_button("📥 Download Reading", data=export_text, file_name="KP_Reading.txt", mime="text/plain")

        with col2:
            share_text = f"I just got a highly accurate KP Horary reading at Astroman AI! My cosmic number was {st.session_state.cosmic_number}. Try yours here: https://astroman-ai.streamlit.app"
            st.link_button("💬 Share on WhatsApp", f"https://wa.me/?text={urllib.parse.quote(share_text)}")

        st.markdown("---")
        st.markdown("### 💬 Ask a Follow-up Question")

        for chat in st.session_state.chat_history:
            with st.chat_message(chat["role"]):
                st.write(chat["content"])

        if follow_up := st.chat_input("Ask for clarifications about this reading..."):
            st.session_state.chat_history.append({"role": "user", "content": follow_up})
            with st.chat_message("user"):
                st.write(follow_up)

            with st.chat_message("assistant"):
                with st.spinner("Consulting the chart..."):
                    try:
                        follow_up_reply = ai_narrator.handle_incoming_message(
                            st.session_state.session_id,
                            follow_up,
                            st.session_state.user_city,
                            st.session_state.cosmic_number
                        )
                        st.write(follow_up_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": follow_up_reply})
                    except Exception as e:
                        st.error(f"Failed to generate response: {e}")

if __name__ == "__main__":
    main()