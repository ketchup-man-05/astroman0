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
- Claim a planet became the Star Lord or Sub Lord because of where it sits. The Star Lord and Sub Lord are fixed in advance by the Horary Number (1-249).
- Invent remedies, behavioral advice, or timing predictions.
- Use outside astrological knowledge to fill gaps or to contradict the JSON.

REQUIRED - you must ONLY:
- Copy signs, house occupations, house ownerships, and points exactly as written in the JSON (the "planets", "house_cusps", "house_ownership", and "step_breakdown" fields).
- Use "kp_score" exactly as given, and the "text" lines in "step_breakdown" for each step's math.
- If "is_retrograde" is true, state that the retrograde Star Lord denies the event, overriding the score.
- If "punarphoo" is true, mention the Saturn-Moon conjunction causing mental anxiety or delay.
- If something is not in the JSON, say that the chart data does not contain it. Do not work it out.

If the numbers seem unusual to you, present them anyway. The JSON is the single source of truth."""

def get_query_houses(user_question):
    """Keyword router mapping questions to standard KP primary & secondary houses."""
    text = user_question.lower()

    if any(word in text for word in ["job", "career", "promotion", "work", "interview", "salary", "business"]):
        return {"positive_houses": [2, 6, 10, 11], "negative_houses": [1, 5, 9, 12]}
    elif any(word in text for word in ["marry", "marriage", "wife", "husband", "wedding", "spouse", "love", "relationship"]):
        return {"positive_houses": [2, 7, 11], "negative_houses": [1, 6, 10]}
    elif any(word in text for word in ["travel", "visa", "abroad", "foreign", "relocate", "pr"]):
        return {"positive_houses": [3, 9, 12], "negative_houses": [2, 4, 11]}
    elif any(word in text for word in ["health", "recover", "sick", "surgery", "disease", "illness", "cure"]):
        return {"positive_houses": [1, 5, 11], "negative_houses": [6, 8, 12]}
    elif any(word in text for word in ["property", "house", "buy", "land", "flat", "vehicle", "car"]):
        return {"positive_houses": [4, 11, 12], "negative_houses": [3, 10]}
    elif any(word in text for word in ["exam", "education", "study", "pass", "result", "test", "admission"]):
        return {"positive_houses": [4, 9, 11], "negative_houses": [3, 8]}
    elif any(word in text for word in ["child", "pregnancy", "baby", "conceive"]):
        return {"positive_houses": [2, 5, 11], "negative_houses": [1, 4, 10]}
    elif any(word in text for word in ["court", "lawsuit", "litigation", "case", "legal", "dispute"]):
        return {"positive_houses": [6, 11], "negative_houses": [12]}
    else:
        return {"positive_houses": [2, 11], "negative_houses": [8, 12]}

def handle_incoming_message(session_id, user_message, city=None, horary_number=None):
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

        house_rules = get_query_houses(user_message)

        chart_data = chart_caster.execute_kp_reading(
            city,
            horary_number,
            house_rules["positive_houses"],
            house_rules["negative_houses"]
        )

        if not chart_data or "error" in chart_data:
            return "System Error: Unable to cast the chart. Please check the city name and Horary Number."

        # The LLM only ever sees the pre-calculated, text-only facts.
        ai_facts = chart_data["ai_facts"]

        initial_prompt = f"""
User Question: "{user_message}"
Location: {city}
Horary Number: {horary_number}

PRE-CALCULATED FACTS (computed by Python; do not recalculate anything):
{json.dumps(ai_facts, indent=2)}

Write your response in exactly two sections using Markdown headers:

### 1. The Verdict
Give a bolded "YES", "NO", or "MIXED" that matches the "verdict" field (DEFINITIVE YES / YES WITH DELAYS -> YES; UNFAVORABLE / NO / DEFINITIVE NO / DENIED -> NO; use MIXED only if the verdict text itself is ambiguous).
Then state the score in exactly this format: "Final KP Score: {ai_facts['kp_score']}"

### 2. KP Mathematical Breakdown
- First, one short line naming the Star Lord and Sub Lord from the "horary" field, and noting they are fixed by the Horary Number.
- Then present the four steps in order by reproducing each "text" line from "step_breakdown" as a clear line item, adding which planet it refers to and, where useful, the planet's sign and house facts copied from "planets" / "house_cusps".
- State the target positive houses and negative houses exactly as listed.
- Apply the retrograde and Punarphoo rules if the flags are true.
- Do not add remedies, advice, or timing predictions.
"""
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