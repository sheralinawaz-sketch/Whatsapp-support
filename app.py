import streamlit as st
import zipfile
import os
import shutil
import io
from gtts import gTTS
from google.generativeai import configure, GenerativeModel

st.set_page_config(layout="wide", page_title="Intelligence Playground & Workspace")

# --- UI Styling ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3, h4, .stSubheader {
        color: #58a6ff !important;
        font-weight: 600;
    }
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        text-align: center;
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 1.2rem;
        font-weight: 700;
    }
    .section-container {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 20px;
    }
    div.stButton > button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 6px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- Storage Architecture ---
BASE_DIR = "contacts_data"
KEY_FILE = "gemini_key.txt"
os.makedirs(BASE_DIR, exist_ok=True)

# --- TTS Helper Function ---
def text_to_speech(text):
    if not text.strip():
        return None
    tts = gTTS(text=text[:1000], lang='en')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

# --- API Key Management ---
api_key = ""
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        api_key = f.read().strip()

st.sidebar.title("⚡ Control Center")
if not api_key:
    user_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
    if st.sidebar.button("Save API Key"):
        if user_key:
            with open(KEY_FILE, "w") as f:
                f.write(user_key)
            st.rerun()
else:
    st.sidebar.caption("API Key Active")
    if st.sidebar.button("Reset Key"):
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        st.rerun()

st.sidebar.divider()

# --- Directory & WhatsApp ZIP Processing ---
def get_contacts():
    return sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])

def extract_and_organize_zip(zip_file, contact_name):
    target_dir = os.path.join(BASE_DIR, contact_name)
    temp_dir = os.path.join(target_dir, "_tmp_extract")
    os.makedirs(temp_dir, exist_ok=True)

    text_dir = os.path.join(target_dir, "Text")
    media_dir = os.path.join(target_dir, "Media")
    audio_dir = os.path.join(target_dir, "Audio")
    for d in [text_dir, media_dir, audio_dir]:
        os.makedirs(d, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    media_exts = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.webp')
    audio_exts = ('.mp3', '.wav', '.opus', '.m4a', '.ogg', '.aac')
    text_exts = ('.txt', '.csv', '.json', '.log')

    for root, _, files in os.walk(temp_dir):
        for f in files:
            source = os.path.join(root, f)
            dest = None
            f_lower = f.lower()

            if f_lower.endswith(text_exts):
                dest = os.path.join(text_dir, f)
            elif f_lower.endswith(media_exts):
                dest = os.path.join(media_dir, f)
            elif f_lower.endswith(audio_exts):
                dest = os.path.join(audio_dir, f)

            if dest:
                shutil.move(source, dest)

    shutil.rmtree(temp_dir, ignore_errors=True)

def get_folder_metrics(contact_name):
    c_path = os.path.join(BASE_DIR, contact_name)
    t_cnt = len(os.listdir(os.path.join(c_path, "Text"))) if os.path.exists(os.path.join(c_path, "Text")) else 0
    m_cnt = len(os.listdir(os.path.join(c_path, "Media"))) if os.path.exists(os.path.join(c_path, "Media")) else 0
    a_cnt = len(os.listdir(os.path.join(c_path, "Audio"))) if os.path.exists(os.path.join(c_path, "Audio")) else 0
    return t_cnt, m_cnt, a_cnt

def aggregate_context(contact_name):
    text_dir = os.path.join(BASE_DIR, contact_name, "Text")
    texts = []
    if os.path.exists(text_dir):
        for f in os.listdir(text_dir):
            if f.endswith('.txt'):
                with open(os.path.join(text_dir, f), 'r', encoding='utf-8', errors='ignore') as file:
                    texts.append(f"--- File: {f} ---\n" + file.read())
    return "\n\n".join(texts)

# --- Sidebar: Contact Navigation & Settings ---
st.sidebar.subheader("Contact Manager")
new_contact = st.sidebar.text_input("New Contact Name:")
if st.sidebar.button("Create Contact") and new_contact:
    sanitized = "".join([c for c in new_contact if c.isalnum() or c in ' -_']).strip()
    if sanitized:
        c_path = os.path.join(BASE_DIR, sanitized)
        os.makedirs(os.path.join(c_path, "Text"), exist_ok=True)
        os.makedirs(os.path.join(c_path, "Media"), exist_ok=True)
        os.makedirs(os.path.join(c_path, "Audio"), exist_ok=True)
        st.rerun()

contacts = get_contacts()

if not contacts:
    st.info("No contacts found. Create a contact from the sidebar to begin.")
    st.stop()

st.sidebar.divider()
st.sidebar.subheader("Speech & Active Focus")
auto_tts = st.sidebar.checkbox("Auto-play Gemini TTS Audio", value=True)
selected_contact = st.sidebar.radio("Select Active Contact:", contacts, key="sidebar_selected_contact")

t_cnt, m_cnt, a_cnt = get_folder_metrics(selected_contact)
st.sidebar.caption(f"Stats for {selected_contact}:")
st.sidebar.text(f"Text Logs: {t_cnt} | Media: {m_cnt} | Audio: {a_cnt}")

# --- Main Interface ---
st.title("Dual-Tier Intelligence Workspace")

# ========================================================
# TOP HALF: Multi-Folder Comparative / Shared Playground
# ========================================================
st.subheader("Shared Multi-Contact Analysis Hub")
with st.expander("Comparative Workspace & Collective Intelligence", expanded=True):
    multi_selected = st.multiselect(
        "Select Contacts for Collective Analysis:",
        options=contacts,
        default=[selected_contact]
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        query_collective = st.text_input("Collective Query / Cross-Analysis Prompt:")
    with col2:
        st.write("")
        st.write("")
        run_collective = st.button("Run Multi-Analysis")

    if run_collective and query_collective:
        if not api_key:
            st.error("Gemini API key is required.")
        elif not multi_selected:
            st.warning("Select at least one contact.")
        else:
            collective_text = ""
            for c in multi_selected:
                ctx = aggregate_context(c)
                if ctx.strip():
                    collective_text += f"\n=== DATA FOR CONTACT: {c} ===\n{ctx[:20000]}\n"

            if collective_text.strip():
                try:
                    configure(api_key=api_key)
                    model = GenerativeModel('gemini-1.5-flash')
                    prompt = f"Analyze data across selected contacts:\n{collective_text}\n\nTask: {query_collective}"
                    with st.spinner("Processing cross-contact analysis..."):
                        resp = model.generate_content(prompt)
                    st.info(resp.text)
                    audio_fp = text_to_speech(resp.text)
                    if audio_fp:
                        st.audio(audio_fp, format='audio/mp3', autoplay=auto_tts)
                except Exception as e:
                    st.error(f"Inference Error: {e}")
            else:
                st.warning("No readable text transcripts found for selected contacts.")

st.divider()

# ========================================================
# BOTTOM HALF: Dedicated Single Contact Workspace & Chat
# ========================================================
st.subheader(f"Dedicated Workspace: {selected_contact}")

col_upload, col_stats = st.columns([2, 1])
with col_upload:
    uploaded_zip = st.file_uploader(
        f"Upload WhatsApp Export ZIP for {selected_contact}:", 
        type=["zip"], 
        key=f"uploader_{selected_contact}"
    )
    if uploaded_zip:
        flag_file = os.path.join(BASE_DIR, selected_contact, f".proc_{uploaded_zip.name}")
        if not os.path.exists(flag_file):
            with st.spinner(f"Extracting WhatsApp archive for {selected_contact}..."):
                extract_and_organize_zip(uploaded_zip, selected_contact)
                with open(flag_file, "w") as f:
                    f.write("ok")
            st.success("Archive unzipped and categorized into Text/, Media/, and Audio/")
            st.rerun()

with col_stats:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-card"><div class="metric-title">Text</div><div class="metric-value">{t_cnt}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-title">Media</div><div class="metric-value">{m_cnt}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-title">Audio</div><div class="metric-value">{a_cnt}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

session_key = f"chat_history_{selected_contact}"
if session_key not in st.session_state:
    st.session_state[session_key] = []

chat_container = st.container(height=380)
for msg in st.session_state[session_key]:
    with chat_container.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

user_prompt = st.chat_input(f"Chat with {selected_contact}'s history...")
if user_prompt:
    st.session_state[session_key].append({"role": "user", "content": user_prompt})
    with chat_container.chat_message("user"):
        st.markdown(user_prompt)

    contact_context = aggregate_context(selected_contact)

    if api_key and contact_context.strip():
        try:
            configure(api_key=api_key)
            model = GenerativeModel('gemini-1.5-flash')
            prompt = (
                f"You are an assistant analyzing WhatsApp communications for contact '{selected_contact}'.\n"
                f"Context Data:\n{contact_context[:35000]}\n\n"
                f"User Question: {user_prompt}"
            )
            response = model.generate_content(prompt)
            bot_reply = response.text
        except Exception as e:
            bot_reply = f"Inference Error: {e}"
    elif not contact_context.strip():
        bot_reply = f"No extracted chat logs found in '{selected_contact}/Text/'. Upload an unencrypted WhatsApp export ZIP above."
    else:
        bot_reply = "API Key not configured in sidebar."

    audio_bytes = None
    if api_key and contact_context.strip():
        tts_stream = text_to_speech(bot_reply)
        if tts_stream:
            audio_bytes = tts_stream.getvalue()

    msg_payload = {"role": "assistant", "content": bot_reply}
    if audio_bytes:
        msg_payload["audio"] = audio_bytes

    st.session_state[session_key].append(msg_payload)
    with chat_container.chat_message("assistant"):
        st.markdown(bot_reply)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=auto_tts)
