import streamlit as st
import os
from google.generativeai import configure, GenerativeModel
st.set_page_config(layout="wide")
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
if api_key:
  configure(api_key=api_key)
  model = GenerativeModel('gemini-1.5-flash')
  st.title("WhatsApp-style Chat")
  st.markdown("""
  <style>
  .chat-row { display: flex; margin-bottom: 10px; }
  .user-row { flex-direction: row-reverse; }
  .bubble { padding: 10px; border-radius: 10px; max-width: 70%; }
  .user-bubble { background-color: #DCF8C6; color: black; }
  .ai-bubble { background-color: #F1F0F0; color: black; }
  </style>
  """, unsafe_allow_html=True)
  if 'messages' not in st.session_state:
  st.session_state.messages = []
  for msg in st.session_state.messages:
  row_class = "user-row" if msg['role'] == 'user' else ""
  bubble_class = "user-bubble" if msg['role'] == 'user' else "ai-bubble"
  st.markdown(f'<div class="chat-row {row_class}"><div class="bubble {bubble_class}">{msg["content"]}</div></div>', unsafe_allow_html=True)
  if prompt := st.chat_input("Type a message..."):
  st.session_state.messages.append({'role': 'user', 'content': prompt})
  st.rerun()
  else:
  st.warning("Please enter your Gemini API Key in the sidebar.")
