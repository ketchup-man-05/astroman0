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

# Active model on your Groq console
MODEL_NAME = "openai/gpt-oss-120b"

# Memory store for active sessions
user_sessions = {}


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
        # Default for general queries / gains
        return {"positive_houses": [2, 11], "negative_houses": [8, 12]}


def handle_incoming_message(user_id, user_message, city=None, horary_number=None):
    current_time = time.time()

    # 1. Session expiration check (20 minutes = 1200 seconds)
    if user_id in user_sessions:
        time_elapsed = current_time - user_sessions[user_id]["last_active"]
        if time_elapsed > 1200:
            del user_sessions[user_id]

    # 2. Scenario A: New Reading (or expired session restart)
    if user_id not in user_sessions:
        if not city or not horary_number:
            return "Your previous session ended. Please enter your question, city, and a Horary Number (1-249) to begin a new chart."

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
You are an expert KP Horary Astrologer providing an analysis inside a web application.

User Question: "{user_message}"
Location: {city}
Horary Number: {horary_number}
Chart Data (Raw KP Engine JSON):
{json.dumps(chart_data, indent=2)}

Target Positive Houses: {house_rules['positive_houses']}
Target Negative Houses: {house_rules['negative_houses']}

Formatting Guidelines:
1. Provide a direct, definitive answer first (Yes, No, or Mixed) based strictly on the 'verdict' and 'kp_score' in the JSON data.
2. Confirm the Horary Seed ({horary_number}) and Judgment Location ({city}).
3. If 'punarphoo' is true in the data, note that the Moon-Saturn connection indicates initial delay, hesitation, or anxiety before the outcome.
4. Detail the planetary significators and houses strictly as reported in the JSON. Do not fabricate house numbers, scores, or planetary strengths.
5. End with an invitation to ask follow-up questions regarding this reading.
"""

        messages = [{"role": "user", "content": initial_prompt}]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.2
        )

        ai_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_reply})

        # Save session context
        user_sessions[user_id] = {
            "messages": messages,
            "chart_data": chart_data,
            "last_active": current_time,
            "count": 0
        }

        return ai_reply

    # 3. Scenario B: Follow-up Questions on the same chart
    else:
        user_data = user_sessions[user_id]

        if user_data["count"] >= 5:
            del user_sessions[user_id]
            return "You have reached the limit of 5 follow-up questions for this chart. Please submit a new question and Horary Number."

        messages = user_data["messages"]
        chart_data = user_data["chart_data"]

        follow_up_prompt = f"""
User Follow-up Question: "{user_message}"

Reference Chart Data:
{json.dumps(chart_data, indent=2)}

Instructions:
Answer this question strictly using the astrological positions, sub-lords, and house significators from this specific cast chart. Do not give generic astrology generalizations.
"""
        messages.append({"role": "user", "content": follow_up_prompt})

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.2
        )

        ai_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_reply})

        user_data["count"] += 1
        user_data["last_active"] = current_time
        user_data["messages"] = messages

        return ai_reply