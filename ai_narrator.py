import json
import time
import streamlit as st
from openai import OpenAI
import chart_caster

# Pull the key securely from Streamlit's hidden vault
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a KP (Krishnamurti Paddhati) Horary report formatter.

Every astrological calculation has ALREADY been performed by a Python engine and is supplied to you as JSON facts. You are NOT an astrologer doing math. You are a formatter and explainer of finished results.

ABSOLUTELY FORBIDDEN - you must NEVER:
- Calculate, infer, or guess a zodiac sign from any degree or number.
- Calculate, infer, or guess which houses a planet owns or rules. Never reason "Sign X is ruled by Planet Y" yourself.
- Decide which house a planet occupies.
- Calculate, add up, adjust, or re-derive any point score. Never do your own arithmetic on the chart.
- Claim a planet became the Cusp Sub Lord or its Star Lord for any reason of your own. They are calculated by the Python engine from the chart and supplied in the "decision" field.
- Invent remedies or behavioral advice.
- Predict, estimate, shift, or infer any date or period yourself. The ONLY timing you may report is the engine-calculated "timing" field in the JSON.
- Soften, remove, or second-guess the "retrograde_rule_note" or the Ruling-Planet caution text already appended to "verdict" - copy them exactly as given.
- Use outside astrological knowledge to fill gaps or to contradict the JSON.

REQUIRED - you must ONLY:
- Copy signs, house occupations, house ownerships, and points exactly as written in the JSON (the "planets", "house_cusps", "house_ownership", "decision", and "step_breakdown" fields).
- Use "kp_score" exactly as given, and the "text" lines in "step_breakdown" for each step's math.
- If "is_retrograde" is true, state that the deciding planet (the Cusp Sub Lord) is retrograde, which indicates delay or obstruction, as already reflected in the verdict.
- If "punarphoo" is true, mention the Saturn-Moon conjunction causing mental anxiety or delay.
- If a "timing" field is present, copy its dasha/bhukti lords, dates, and "text" lines exactly as written. If "timing" contains an "error", say that timing is unavailable for this chart.
- If something is not in the JSON, say that the chart data does not contain it. Do not work it out.

If the numbers seem unusual to you, present them anyway. The JSON is the single source of truth."""

import re

# Words that would otherwise prefix-match an unrelated longer word (pass -> passport) get an
# explicit "not followed by this" exception instead of the default open-ended prefix match.
_PREFIX_EXCEPTIONS = {"pass": "port"}

def _has_any(text, words):
    """Whole-word keyword match (so 'land' does not match 'England', 'test' not 'latest').
    Words of 3 letters or fewer must match exactly (optional plural 's'); longer words
    match from the start of a word, so 'recover' also catches 'recovered' and 'marri'
    catches 'married'/'marriage'. A word in _PREFIX_EXCEPTIONS also excludes its listed
    continuation (e.g. 'pass' matches 'passed'/'passing' but not 'passport')."""
    for w in words:
        if w in _PREFIX_EXCEPTIONS:
            pattern = rf"\b{w}(?!{_PREFIX_EXCEPTIONS[w]})\w*\b"
        elif len(w) <= 3:
            pattern = rf"\b{w}s?\b"
        else:
            pattern = rf"\b{w}"
        if re.search(pattern, text):
            return True
    return False

# Most keyword hits wins; ties keep the original topic order.
def _count_hits(text, words):
    """Number of distinct topic keywords matching (same rules as _has_any)."""
    return sum(1 for w in words if _has_any(text, [w]))
TOPICS = [
    ("career",   ["job", "career", "promotion", "work", "interview", "salary", "business",
                  "employ", "hire", "hiring", "startup"],
                 [2, 6, 10, 11], [1, 5, 9, 12], 10),
    ("marriage", ["marry", "marri", "wife", "husband", "wedding", "spouse", "love", "relationship",
                  "partner", "boyfriend", "girlfriend", "fiance", "engagement", "engaged"],
                 [2, 7, 11], [1, 6, 10], 7),
    ("travel",   ["travel", "visa", "abroad", "foreign", "relocate", "pr", "passport",
                  "immigra", "emigra", "migrat", "overseas", "canada", "usa", "uk", "england",
                  "australia", "germany", "dubai", "america", "europe"],
                 [3, 9, 12], [2, 4, 11], 12),
    ("health",   ["health", "recover", "sick", "surgery", "disease", "illness", "cure",
                  "medic", "doctor", "hospital", "treatment", "heal"],
                 [1, 5, 11], [6, 8, 12], 6),
    ("property", ["property", "house", "buy", "land", "flat", "vehicle", "car",
                  "apartment", "plot", "bike", "scooter"],
                 [4, 11, 12], [3, 10], 4),
    ("exam",     ["exam", "education", "study", "studi", "pass", "result", "test", "admission",
                  "marks", "rank", "college", "university", "scholarship", "degree"],
                 [4, 9, 11], [3, 8], 4),
    ("children", ["child", "pregnan", "baby", "babies", "conceiv"],
                 [2, 5, 11], [1, 4, 10], 5),
    ("court",    ["court", "lawsuit", "litigation", "legal", "dispute", "lawyer", "judge",
                  "court case", "legal case", "criminal case", "civil case"],
                 [6, 11], [12], 6),
]
DEFAULT_HOUSES = ([2, 11], [8, 12])   # money / general - used when nothing matches
DEFAULT_KEY_HOUSE = 11                # 11th = fulfilment of desire

# Each TOPICS row is: (name, keywords, positive houses, negative houses, KEY HOUSE).
# The KEY HOUSE is the cusp whose SUB LORD decides the answer in KP horary.

# Labels for the optional topic dropdown in the app (None = detect from the question)
TOPIC_OPTIONS = {
    "Auto-detect from my question": None,
    "Career / Job / Business": "career",
    "Marriage / Relationship": "marriage",
    "Travel / Visa / Abroad": "travel",
    "Health / Recovery": "health",
    "Property / Vehicle": "property",
    "Exam / Education": "exam",
    "Children / Pregnancy": "children",
    "Court case / Legal": "court",
    "Money / Anything else": "general",
}

def get_query_houses(user_question, topic=None):
    """Maps a question (or an explicitly chosen topic) to standard KP positive & negative houses."""
    if topic == "general":
        return {"positive_houses": list(DEFAULT_HOUSES[0]), "negative_houses": list(DEFAULT_HOUSES[1]), "key_house": DEFAULT_KEY_HOUSE}
    if topic:
        for key, _, pos, neg, kh in TOPICS:
            if key == topic:
                return {"positive_houses": list(pos), "negative_houses": list(neg), "key_house": kh}

    text = user_question.lower()
    best = None  # (hits, order, pos, neg, key_house)
    for order, (_, keywords, pos, neg, kh) in enumerate(TOPICS):
        hits = _count_hits(text, keywords)
        if hits and (best is None or hits > best[0]):
            best = (hits, order, pos, neg, kh)
    if best is not None:
        _, _, pos, neg, kh = best
        return {"positive_houses": list(pos), "negative_houses": list(neg), "key_house": kh}
    return {"positive_houses": list(DEFAULT_HOUSES[0]), "negative_houses": list(DEFAULT_HOUSES[1]), "key_house": DEFAULT_KEY_HOUSE}

def handle_incoming_message(session_id, user_message, city=None, horary_number=None, topic=None):
    current_time = time.time()
    
    # Ensure session dict exists (failsafe if imported weirdly)
    if "user_sessions" not in st.session_state:
        st.session_state.user_sessions = {}

    # --- 1. HANDLE SESSION TIMEOUTS ---
    is_follow_up = session_id in st.session_state.user_sessions
    
    if is_follow_up:
        time_elapsed = current_time - st.session_state.user_sessions[session_id]["last_active"]
        if time_elapsed > 1200:  # 20 minutes
            del st.session_state.user_sessions[session_id]
            is_follow_up = False
            return "Your cosmic connection has timed out (20 minutes). Please click 'Cast Horary Chart & Analyze' to re-align the stars."

    # --- 2. PRIMARY CAST (NEW CHART) ---
    if not is_follow_up:
        if not city or not horary_number:
            return "System Error: Missing City or Horary Number to cast a new chart."

        house_rules = get_query_houses(user_message, topic)

        chart_data = chart_caster.execute_kp_reading(
            city,
            horary_number,
            house_rules["positive_houses"],
            house_rules["negative_houses"],
            house_rules["key_house"]
        )

        if not chart_data or "error" in chart_data:
            return "System Error: Unable to cast the chart. Please check the city name and Horary Number."

        # The LLM only ever sees the pre-calculated, text-only facts.
        ai_facts = chart_data["ai_facts"]

        has_timing = bool(ai_facts.get("timing"))
        section_count = "three sections" if has_timing else "two sections"
        timing_instructions = ""
        if has_timing:
            timing_instructions = """
### 3. Timing (Vimshottari dasha at the query moment)
- State the Moon's sign, star lord, and the Mahadasha at the chart moment with its balance, copied from "timing.moon".
- Reproduce the "text" line of "timing.active" as the current period, and say whether "qualifies" is true or false.
- Reproduce the "text" line of "timing.next_supportive" as the next supporting period. If it is null, say no supporting period was found in the searched range.
- If "timing.upcoming_supportive" has more entries, list their "text" lines in order.
- For each entry in "timing.upcoming_supportive", also reproduce its "antara_text" line right after its "text" line.
- Reproduce the "text" line of "timing.next_supportive_antara" as the finest supportive window. If it is null, say no supportive antara was found in the searched range.
- If "timing.active" has an "antara_text" field, reproduce it as the currently running antara.
- If "transit_confirmation" is present and has no "error", reproduce its "text" as a gochar cross-check and state its "classification"; say plainly that it does not change the verdict. If it has an "error" or an "at_next_antara" entry, mention the future-window check briefly.
- Copy "timing.note" exactly. Do not estimate or adjust any date. If "timing" contains an "error", write only that timing is unavailable.
"""
        initial_prompt = f"""
User Question: "{user_message}"
Location: {city}
Horary Number: {horary_number}

PRE-CALCULATED FACTS (computed by Python; do not recalculate anything):
{json.dumps(ai_facts, indent=2)}

Write your response in exactly {section_count} using Markdown headers:

### 1. The Verdict
Give a bolded "YES", "NO", "MIXED", or "DELAYED" that matches the "verdict" field (DEFINITIVE YES / YES WITH DELAYS -> YES; UNFAVORABLE / NO / DEFINITIVE NO -> NO; MIXED / CONFLICTING or MIXED / UNCLEAR -> MIXED; DELAYED, NOT DENIED -> DELAYED, and explain in one line that this project treats retrograde as a delay signal, not a denial). If "decision.ruling_planet_support" is false and the verdict is YES-leaning, keep the caution sentence that is already appended to "verdict" - do not drop it for brevity.
Then state the score in exactly this format: "Final KP Score: {ai_facts['kp_score']}"

### 2. KP Mathematical Breakdown
- First, one short line naming the key house, its Cusp Sub Lord (the deciding planet) and that planet's Star Lord from the "decision" field, noting the engine calculated them from the chart. If "decision.note" is not empty, include it.
- Then present the four steps in order by reproducing each "text" line from "step_breakdown" as a clear line item, adding which planet it refers to and, where useful, the planet's sign and house facts copied from "planets" / "house_cusps".
- State the target positive houses and negative houses exactly as listed.
- Apply the retrograde and Punarphoo rules if the flags are true.
- Include the "ruling_planet_check" text line exactly as written; it is confirmation only and does not change the score.
- Do not add remedies or advice.
{timing_instructions}"""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": initial_prompt},
        ]

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1 
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            return f"System Error: The AI Oracle failed to respond. Check API keys and model names. (System flag: {str(e)})"

        messages.append({"role": "assistant", "content": ai_reply})

        # Save session (full chart_data kept for the UI; only ai_facts goes to the LLM)
        st.session_state.user_sessions[session_id] = {
            "messages": messages,
            "chart_data": chart_data,
            "last_active": current_time,
            "count": 0
        }
        return ai_reply

    # --- 3. FOLLOW-UP CHAT ---
    else:
        user_data = st.session_state.user_sessions[session_id]

        if user_data["count"] >= 5:
            return "You have reached the limit of 5 follow-up questions for this chart. Please submit a new question to cast a fresh chart."

        messages = user_data["messages"]
        ai_facts = user_data["chart_data"]["ai_facts"]

        follow_up_prompt = f"""
User Follow-up Question: "{user_message}"

PRE-CALCULATED FACTS (unchanged; do not recalculate anything):
{json.dumps(ai_facts, indent=2)}

Instructions:
Answer using only the facts above, quoting signs, house occupations, house ownerships, and points exactly as written. Do not calculate or infer any sign, ownership, or score yourself. If answering would require a new score or facts not in the JSON (for example, judging a different topic than the original question), say that a fresh chart must be cast for that. Keep a clinical, factual tone.
"""
        messages.append({"role": "user", "content": follow_up_prompt})

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1
            )
            ai_reply = response.choices[0].message.content
        except Exception as e:
            messages.pop() # Safely remove the failed user prompt from memory
            return f"System Error: Follow-up failed. (System flag: {str(e)})"

        messages.append({"role": "assistant", "content": ai_reply})

        user_data["count"] += 1
        user_data["last_active"] = current_time
        user_data["messages"] = messages

        return ai_reply