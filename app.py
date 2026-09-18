import streamlit as st
import uuid
import ai_narrator

st.set_page_config(page_title="KP Horary Astrology AI", page_icon="🔮", layout="centered")

# Initialize session ID so each visitor gets isolated astrology memory
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "reading_done" not in st.session_state:
    st.session_state.reading_done = False
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🔮 KP Horary Astrology AI")
st.caption("Ask your question, provide your location, and pick a horary seed (1–249).")

# Step 1: Initial Chart Reading
if not st.session_state.reading_done:
    with st.form("astrology_form"):
        question = st.text_input("Your Question", placeholder="e.g. Will I get this job?")
        city = st.text_input("Your Current City", placeholder="e.g. Shimla")
        horary_number = st.number_input("Horary Number (1 to 249)", min_value=1, max_value=249, value=45, step=1)
        
        submitted = st.form_submit_button("Cast Horary Chart & Analyze")
        
        if submitted:
            if not question or not city:
                st.error("Please fill in both your question and city.")
            else:
                with st.spinner("Calculating planetary cusps and querying AI..."):
                    try:
                        reply = ai_narrator.handle_incoming_message(
                            st.session_state.session_id, question, city, int(horary_number)
                        )
                        st.session_state.reading_done = True
                        st.session_state.messages.append({"role": "user", "content": f"{question} ({city}, #{horary_number})"})
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error calculating reading: {e}")

# Step 2: Interactive Chat for Follow-Up Questions
else:
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input for follow-up questions
    if prompt := st.chat_input("Ask a follow-up question about this chart..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Consulting the chart..."):
                reply = ai_narrator.handle_incoming_message(st.session_state.session_id, prompt)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

    st.divider()
    if st.button("Start a New Reading"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.reading_done = False
        st.session_state.messages = []
        st.rerun()