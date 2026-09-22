import streamlit as st
import urllib.parse
import uuid
import time
from typing import Any
import html

# Ensure these modules are available in your directory
import ai_narrator
import chart_caster

# ----------------------------------------------------------------------
# 1. Page Configuration & CSS
# ----------------------------------------------------------------------
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
    .kundli-grid {
        display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(4, 80px);
        gap: 2px; background-color: #475569; border: 2px solid #475569; border-radius: 8px; margin-bottom: 20px;
    }
    .kundli-box {
        background-color: #0F172A; padding: 4px; font-size: 11px; font-weight: 600; color: #E2E8F0; overflow: hidden;
    }
    .kundli-empty { background-color: #1E293B; }
    div[data-testid="stRadio"] { display: flex; justify-content: center; margin-bottom: 10px; }
    .stAlert { background-color: #1E293B !important; border: 1px solid #334155 !important; color: #F8FAFC !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 2. Session State Initialization Wrapper
# ----------------------------------------------------------------------
def _ensure(key: str, default: Any) -> Any:
    """Return existing session_state[key] or set it to default safely."""
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]

_ensure("session_id", str(uuid.uuid4()))
_ensure("user_sessions", {})
_ensure("chat_history", [])
_ensure("reading_done", False)
_ensure("question_input", "")
_ensure("user_city", "Shimla")
_ensure("cosmic_number", 45)
_ensure("raw_planets", None)
_ensure("raw_ascendant", None)
_ensure("reading_result", "")

# ----------------------------------------------------------------------
# 3. Cached Functions & UI Helpers
# ----------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def _load_live_weather(lon: float = 77.17) -> str:
    """Cache the live weather. 'lon' defaults to Shimla's longitude."""
    day_name, day_lord = chart_caster.get_current_day_lord(lon)
    planets, _ = chart_caster.get_live_planets()
    tithi = chart_caster.get_panchang_tithi(planets["Sun"], planets["Moon"])
    return f"🌙 {tithi} | ☀️ Day of {day_name} ({day_lord})"

def draw_north_indian_chart(planets_dict, ascendant_lon):
    """Generates an SVG North Indian style diamond chart for Dark Mode."""
    if ascendant_lon is None: return ""
    
    asc_sign = int(ascendant_lon // 30)
    house_planets = {h: [] for h in range(1, 13)}
    
    for p, lon in planets_dict.items():
        p_sign = int(lon // 30)
        h = (p_sign - asc_sign) % 12 + 1
        house_planets[h].append(html.escape(p[:2]))
        
    def get_txt(h): return ", ".join(house_planets[h])
    def get_num(h): return (asc_sign + h - 1) % 12 + 1
        
    svg = f"""<div style="display:flex; justify-content:center; margin-bottom: 20px;"><svg viewBox="0 0 400 400" width="100%" max-width="400px" style="background-color: #1E293B; border: 2px solid #475569; border-radius: 8px;"><rect x="0" y="0" width="400" height="400" fill="none" stroke="#64748B" stroke-width="2"/><line x1="0" y1="0" x2="400" y2="400" stroke="#64748B" stroke-width="2"/><line x1="400" y1="0" x2="0" y2="400" stroke="#64748B" stroke-width="2"/><polygon points="200,0 400,200 200,400 0,200" fill="none" stroke="#64748B" stroke-width="2"/><text x="200" y="110" text-anchor="middle" font-size="14" font-weight="bold" fill="#60A5FA">{get_txt(1)}</text><text x="200" y="25" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(1)}</text><text x="100" y="60" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(2)}</text><text x="175" y="25" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(2)}</text><text x="60" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(3)}</text><text x="20" y="175" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(3)}</text><text x="110" y="200" text-anchor="middle" font-size="14" font-weight="bold" fill="#E2E8F0">{get_txt(4)}</text><text x="20" y="200" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(4)}</text><text x="60" y="300" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(5)}</text><text x="20" y="225" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(5)}</text><text x="100" y="350" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(6)}</text><text x="175" y="385" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(6)}</text><text x="200" y="310" text-anchor="middle" font-size="14" font-weight="bold" fill="#E2E8F0">{get_txt(7)}</text><text x="200" y="385" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(7)}</text><text x="300" y="350" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(8)}</text><text x="225" y="385" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(8)}</text><text x="350" y="300" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(9)}</text><text x="385" y="225" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(9)}</text><text x="290" y="200" text-anchor="middle" font-size="14" font-weight="bold" fill="#E2E8F0">{get_txt(10)}</text><text x="385" y="200" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(10)}</text><text x="350" y="100" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(11)}</text><text x="385" y="175" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(11)}</text><text x="300" y="60" text-anchor="middle" font-size="12" font-weight="bold" fill="#E2E8F0">{get_txt(12)}</text><text x="225" y="25" text-anchor="middle" font-size="11" fill="#94A3B8">{get_num(12)}</text></svg></div>"""
    return svg

def draw_south_indian_chart(planets_dict):
    """Generates an HTML South Indian style chart grid for Dark Mode."""
    sign_placements = {i: [] for i in range(12)}
    for planet, lon in planets_dict.items():
        sign = int(lon // 30)
        sign_placements[sign].append(html.escape(planet[:2]))
        
    def box(sign_idx):
        planets = ", ".join(sign_placements[sign_idx])
        return f'<div class="kundli-box">{planets}</div>'

    html_out = f"""<div class="kundli-grid">{box(11)} {box(0)} {box(1)} {box(2)} {box(10)} <div class="kundli-box kundli-empty" style="grid-column: span 2; grid-row: span 2; display:flex; align-items:center; justify-content:center; font-size:14px; color:#94A3B8;">Rasi Chart</div> {box(3)} {box(9)} {box(4)} {box(8)} {box(7)} {box(6)} {box(5)}</div>"""
    return html_out

# ----------------------------------------------------------------------
# 4. Main App UI
# ----------------------------------------------------------------------
st.title("✨ Astroman AI: KP Horary")

# Cosmic Weather Widget
try:
    weather_info = _load_live_weather()
    st.info(f"**Live Cosmic Weather (Shimla):** {weather_info}")
except Exception as e:
    st.warning(f"Cosmic Weather sync delayed. (System note: {e})")

# Intent-Based Question Categories
st.markdown("##### What is on your mind? (Quick Select)")
c1, c2, c3, c4 = st.columns(4)

def set_question(q: str):
    st.session_state.question_input = q

if c1.button("💼 Career"): set_question("Will I secure the job after yesterday's interview?")
if c2.button("❤️ Love"): set_question("Will my current relationship lead to marriage?")
if c3.button("💰 Wealth"): set_question("Will my upcoming business deal be profitable?")
if c4.button("📚 Exams"): set_question("Will I pass my upcoming competitive exam?")

# Main Horary Form
with st.form("astrology_form"):
    question = st.text_input("Your Question", value=st.session_state.question_input, placeholder="e.g. Will I get this job?")
    city = st.text_input("Your Current City", value=st.session_state.user_city)
    
    horary_number = st.number_input(
        "Your Cosmic Number (1 to 249)", 
        min_value=1, max_value=249, value=st.session_state.cosmic_number, step=1,
        help="Close your eyes, focus deeply on your question, and type the very first number between 1 and 249."
    )
    
    submitted = st.form_submit_button("Cast Horary Chart & Analyze")

# ----------------------------------------------------------------------
# 5. Form Submission & Mystic Loading
# ----------------------------------------------------------------------
if submitted:
    if not question or not city:
        st.error("Please fill in both your question and city.")
    else:
        # THE FIX: Generate a brand new Session ID to force a fresh chart calculation
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
                # Direct positional arguments to bypass module caching issues
                reply = ai_narrator.handle_incoming_message(
                    st.session_state.session_id, 
                    question, 
                    city, 
                    int(horary_number)
                )
                
                session_data = st.session_state.user_sessions.get(st.session_state.session_id, {})
                chart_metadata = session_data.get("chart_data", {}).get("chart_data", {})
                
                if chart_metadata:
                    st.session_state.raw_planets = chart_metadata.get("planets")
                    cusps = chart_metadata.get("cusps")
                    st.session_state.raw_ascendant = cusps[0] if cusps else None
                else:
                    st.session_state.raw_planets = None
                    st.session_state.raw_ascendant = None
                
                st.session_state.reading_result = reply
                st.session_state.reading_done = True
                status.update(label="Cosmic Alignment Complete!", state="complete", expanded=False)
                
            except Exception as e:
                status.update(label="Disturbance in the cosmos", state="error")
                st.error(f"Error calculating reading: {e}")

# ----------------------------------------------------------------------
# 6. Display Results & Social Features
# ----------------------------------------------------------------------
if st.session_state.reading_done:
    st.markdown("---")
    st.markdown("### 📜 Your Cosmic Reading")
    
    if st.session_state.raw_planets and st.session_state.raw_ascendant is not None:
        chart_style = st.radio("Chart Style", ["North Indian", "South Indian"], horizontal=True, label_visibility="collapsed")
        
        try:
            if chart_style == "North Indian":
                st.markdown(draw_north_indian_chart(st.session_state.raw_planets, st.session_state.raw_ascendant), unsafe_allow_html=True)
            else:
                st.markdown(draw_south_indian_chart(st.session_state.raw_planets), unsafe_allow_html=True)
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
                    # Direct positional arguments for the follow-up
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