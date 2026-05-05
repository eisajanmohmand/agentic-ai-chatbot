import streamlit as st
from agents import route_message, run_agent

AGENT_LABELS = {
    "symptom": "🩺 Symptom Analysis Agent",
    "medication": "💊 Medication Safety Agent",
    "emergency": "🚑 Emergency Decision Agent",
}

st.set_page_config(page_title="Medical AI Chatbot", page_icon="🏥")
st.title("🏥 Agentic Medical Chatbot")
st.caption("Powered by 3 specialized AI agents: Symptom Analysis · Medication Safety · Emergency Detection")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_used" not in st.session_state:
    st.session_state.agent_used = []

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and i // 2 < len(st.session_state.agent_used):
            agent_key = st.session_state.agent_used[i // 2]
            st.caption(f"Agent: {AGENT_LABELS.get(agent_key, '')}")
        st.markdown(msg["content"])

if prompt := st.chat_input("Describe your symptoms, ask about a medicine, or report an emergency..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            agent_type = route_message(prompt)
            # Always check for emergency regardless of routing
            if agent_type != "emergency":
                emergency_keywords = ["chest pain", "can't breathe", "cannot breathe", "stroke", "unconscious", "severe bleeding", "not breathing", "heart attack"]
                if any(kw in prompt.lower() for kw in emergency_keywords):
                    agent_type = "emergency"

            conversation = [m for m in st.session_state.messages]
            response = run_agent(agent_type, conversation)

        st.caption(f"Agent: {AGENT_LABELS.get(agent_type, '')}")
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.agent_used.append(agent_type)

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This chatbot routes your message to the right agent:

    - 🩺 **Symptom Agent** — analyzes symptoms, asks follow-ups, estimates urgency
    - 💊 **Medication Agent** — explains medicines, side effects, interactions
    - 🚑 **Emergency Agent** — detects emergencies, advises immediate action

    ---
    ⚠️ *This is not a substitute for professional medical advice.*
    """)

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.agent_used = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Set your API key** via environment variable `OPENAI_API_KEY`")
