import streamlit as st
import base64
from agents import route_message, run_agent

AGENT_LABELS = {
    "symptom": "🩺 Symptom Analysis Agent",
    "medication": "💊 Medication Safety Agent",
    "emergency": "🚑 Emergency Decision Agent",
}

EMERGENCY_KEYWORDS = ["chest pain", "can't breathe", "cannot breathe", "stroke",
                      "unconscious", "severe bleeding", "not breathing", "heart attack"]

st.set_page_config(page_title="Medical AI Chatbot", page_icon="🏥", layout="wide")

# --- Session state init ---
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = None
if "processed_upload" not in st.session_state:
    st.session_state.processed_upload = None

def new_chat():
    import time
    cid = str(int(time.time() * 1000))
    st.session_state.chats[cid] = {"title": "New Chat", "messages": [], "agents": []}
    st.session_state.current_chat = cid
    st.session_state.processed_upload = None

if st.session_state.current_chat is None:
    new_chat()

cid = st.session_state.current_chat
chat = st.session_state.chats[cid]

# --- Sidebar ---
with st.sidebar:
    st.title("🏥 Medical AI")
    if st.button("✏️ New Chat", use_container_width=True):
        new_chat()
        st.rerun()

    st.markdown("---")
    st.markdown("**Chat History**")
    for hid, hchat in reversed(list(st.session_state.chats.items())):
        label = hchat["title"]
        is_active = hid == st.session_state.current_chat
        btn_label = f"▶ {label}" if is_active else label
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(btn_label, key=f"hist_{hid}", use_container_width=True):
                st.session_state.current_chat = hid
                st.rerun()
        with col2:
            if st.button("🗑", key=f"del_{hid}"):
                del st.session_state.chats[hid]
                if st.session_state.current_chat == hid:
                    remaining = list(st.session_state.chats.keys())
                    st.session_state.current_chat = remaining[-1] if remaining else None
                st.rerun()

    st.markdown("---")
    st.caption("⚠️ Not a substitute for professional medical advice.")

# --- Main area ---
st.title("🏥 Agentic Medical Chatbot")

# Display existing messages
for i, msg in enumerate(chat["messages"]):
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=300)
        if msg.get("content"):
            st.markdown(msg["content"])
        if msg["role"] == "assistant":
            agent_idx = sum(1 for m in chat["messages"][:i] if m["role"] == "assistant")
            if agent_idx < len(chat["agents"]):
                st.caption(f"Agent: {AGENT_LABELS.get(chat['agents'][agent_idx], '')}")

# --- Image upload ---
uploaded_file = st.file_uploader("📎 Attach a disease image (optional)", type=["jpg", "jpeg", "png", "webp"], label_visibility="collapsed")

# --- Chat input ---
prompt = st.chat_input("Describe symptoms, ask about medicine, or attach a disease image above...")

# Prevent re-processing the same upload on reruns
if uploaded_file and uploaded_file.name == st.session_state.processed_upload and not prompt:
    uploaded_file = None

if prompt or uploaded_file:
    image_bytes = None
    image_b64 = None
    image_mime = None

    if uploaded_file:
        image_bytes = uploaded_file.read()
        image_mime = uploaded_file.type
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        st.session_state.processed_upload = uploaded_file.name

    user_text = prompt or "Analyze this image for any visible disease or medical condition."

    # Show user message
    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes, width=300)
        st.markdown(user_text)

    # Save user message
    chat["messages"].append({"role": "user", "content": user_text, "image": image_bytes})
    if chat["title"] == "New Chat" and prompt:
        chat["title"] = prompt[:35]

    # Build conversation history for agent
    history = [{"role": m["role"], "content": m["content"]} for m in chat["messages"]]

    # Route
    agent_type = route_message(user_text)
    if agent_type != "emergency" and any(kw in user_text.lower() for kw in EMERGENCY_KEYWORDS):
        agent_type = "emergency"

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = run_agent(agent_type, history, image_b64, image_mime)
        st.markdown(response)
        st.caption(f"Agent: {AGENT_LABELS.get(agent_type, '')}")

    chat["messages"].append({"role": "assistant", "content": response, "image": None})
    chat["agents"].append(agent_type)
    st.rerun()
