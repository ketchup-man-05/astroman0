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
MODEL_NAME = "llama3-70b-8192"

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
        return {"positive_houses": [2, 11], "negative_houses": [8, 12]}


def handle_incoming_message(user_id, user_message, city=None, horary_number=None):
    current_time = time.time()

    if user_id in user_sessions:
        time_elapsed = current_time - user_sessions[user_id]["last_active"]
        if time_elapsed > 1200:
            del user_sessions[user_id]

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
You are an elite, premium KP (Krishnamurti Paddhati) Horary Astrologer. 
Your tone is highly professional, decisive, and clinical, similar to a high-end consultant.

User Question: "{user_message}"
Location: {city}
Horary Number: {horary_number}
Chart Data (Raw KP Engine JSON):
{json.dumps(chart_data, indent=2)}

Target Positive Houses: {house_rules['positive_houses']}
Target Negative Houses: {house_rules['negative_houses']}

You MUST structure your response in exactly four distinct sections using Markdown headers:

### 1. The Verdict
Give a definitive, bolded "YES", "NO", or "MIXED" based strictly on the 'verdict' and 'kp_score' in the JSON data. Do not be vague.

### 2. Astrological Breakdown
In 2 or 3 brief bullet points, explain the "why":
- Detail the specific planetary significators, sub-lords, and houses as reported in the JSON.
- If 'punarphoo' is true, note that the Moon-Saturn connection indicates initial delay, hesitation, or anxiety before the outcome.

### 3. Timing of the Event (The 'When')
Using the 'ruling_planets' data provided in the JSON (Ascendant Lord, Moon Lord, Day Lord) and the current Panchang data, provide a brief estimate of WHEN this event is most likely to occur or when the energetic window opens. If the verdict is NO, state that the current planetary periods do not support a timeline for success.

### 4. Remedy & Action Protocol
Provide a highly practical, actionable piece of advice based on the verdict:
- If NO: Give a behavioral remedy to mitigate the failure.
- If YES: Give an action to secure the win.

Do not include any introductory filler text. End by inviting follow-up questions.
"""

        messages = [{"role": "user", "content": initial_prompt}]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.2 
        )

        ai_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_reply})

        user_sessions[user_id] = {
            "messages": messages,
            "chart_data": chart_data,
            "last_active": current_time,
            "count": 0
        }

        return ai_reply

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
Answer this question strictly using the astrological positions, sub-lords, and house significators from this specific cast chart. Do not give generic astrology generalizations. Maintain your professional, premium consultant tone.
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