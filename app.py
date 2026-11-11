import streamlit as st
import os
from google.generativeai import configure, GenerativeModel
from PIL import Image

st.set_page_config(layout="wide")

# --- Sidebar: Setup and Personas ---
st.sidebar.title("Chat Settings")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

# Set up the dictionary to hold different people's chats
if 'chats' not in st.session_state:
    st.session_state.chats = {"General Chat": []}
if 'current_person' not in st.session_state:
    st.session_state.current_person = "General Chat"

st.sidebar.divider()
st.sidebar.subheader("Manage People")

# 1. Create a new person
new_person = st.sidebar.text_input("Add new person's name:")
if st.sidebar.button("Create Chat") and new_person:
    if new_person not in st.session_state.chats:
        st.session_state.chats[new_person] = []
        st.session_state.current_person = new_person
        st.rerun()

# 2. Switch between people
st.session_state.current_person = st.sidebar.selectbox(
    "Select Active Chat:",
    options=list(st.session_state.chats.keys()),
    index=list(st.session_state.chats.keys()).index(st.session_state.current_person)
)

# --- Main App ---
if api_key:
    configure(api_key=api_key)
    model = GenerativeModel('gemini-1.5-flash')

    st.title(f"Chatting with: {st.session_state.current_person}")
    
    st.markdown("""
        <style>
        .chat-row { display: flex; margin-bottom: 10px; }
        .user-row { flex-direction: row-reverse; }
        .bubble { padding: 10px; border-radius: 10px; max-width: 70%; margin: 5px; }
        .user-bubble { background-color: #DCF8C6; color: black; }
        .ai-bubble { background-color: #F1F0F0; color: black; }
        </style>
    """, unsafe_allow_html=True)

    # Load only the active person's messages
    current_messages = st.session_state.chats[st.session_state.current_person]

    for msg in current_messages:
        row_class = "user-row" if msg['role'] == 'user' else ""
        bubble_class = "user-bubble" if msg['role'] == 'user' else "ai-bubble"
        st.markdown(f'<div class="chat-row {row_class}"><div class="bubble {bubble_class}">{msg["content"]}</div></div>', unsafe_allow_html=True)

    # 3. Media Uploader (The "+" button alternative)
    media_file = st.file_uploader("➕ Attach Media", type=['png', 'jpg', 'jpeg', 'mp3', 'mp4', 'wav'])

    if prompt := st.chat_input("Type a message..."):
        # Save user message to this specific person's chat
        current_messages.append({'role': 'user', 'content': prompt})
        
        # Format the history so Gemini remembers only this person's context
        history = []
        for m in current_messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})
        
        try:
            # Start chat with this specific person's history
            chat_session = model.start_chat(history=history)
            
            # If an image is attached, send it alongside the text
            if media_file and media_file.type.startswith('image'):
                img = Image.open(media_file)
                response = model.generate_content([prompt, img])
            else:
                # Send text normally
                response = chat_session.send_message(prompt)
                
            current_messages.append({'role': 'ai', 'content': response.text})
        except Exception as e:
            current_messages.append({'role': 'ai', 'content': f"Error: {e}"})
            
        st.rerun()
else:
    st.warning("Please enter your Gemini API Key in the sidebar.")
