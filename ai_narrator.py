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

# THE LION'S FIX: Use a real, highly capable Groq model. 
MODEL_NAME = "openai/gpt-oss-120b"

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

        initial_prompt = f"""
You are an elite, highly clinical KP (Krishnamurti Paddhati) Astrologer. Your job is to act as a strict mathematical interpreter of the provided KP Horary data.

User Question: "{user_message}"
Location: {city}
Horary Number: {horary_number}
Target Positive Houses: {house_rules['positive_houses']}
Target Negative Houses: {house_rules['negative_houses']}

Chart Data (Raw KP Engine JSON):
{json.dumps(chart_data, indent=2)}

You MUST structure your response in exactly two distinct sections using Markdown headers:

### 1. The Verdict
Give a definitive, bolded "YES", "NO", or "MIXED". 
You MUST explicitly state the final KP Score by reading the exact 'kp_score' value from the JSON data. Format it exactly like this: "Final KP Score: [Insert Score Here]". 
CRITICAL RULE: DO NOT calculate the score yourself. Trust the JSON 'kp_score' completely. 

### 2. KP Mathematical Breakdown
Explain the exact math that led to this score by matching the houses in the 4 Steps against the Target Positive and Negative houses. Be transparent about why points were awarded or NOT awarded.
- Step 1 (Star Lord Occupation)
- Step 2 (Star Lord Ownership)
- Step 3 (Sub Lord Occupation)
- Step 4 (Sub Lord Ownership)
If a house was neutral (not in the positive/negative lists), explicitly state that it received 0 points.
- If 'is_retrograde' is true, explicitly state that the Retrograde Star Lord denies the event entirely, regardless of the score.
- If 'punarphoo' is true, mention the Saturn-Moon conjunction causing mental anxiety or delay.

DO NOT invent remedies, behavioral advice, or timing predictions. Stick strictly to the mathematical proof of the chart.
"""
        messages = [{"role": "user", "content": initial_prompt}]

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

        # Save session
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
        chart_data = user_data["chart_data"]

        follow_up_prompt = f"""
User Follow-up Question: "{user_message}"

Reference Chart Data:
{json.dumps(chart_data, indent=2)}

Instructions:
Answer this question strictly using the mathematical positions from this chart. Do not give generalizations. Maintain a clinical, mathematical tone.
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