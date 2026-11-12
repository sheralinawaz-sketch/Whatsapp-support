import os
import shutil
import zipfile
import io
import streamlit as st
import requests
from gtts import gTTS

# Platform Limits & Configuration Constants
STREAMLIT_MAX_FILE_SIZE_MB = 200
CHUNK_SIZE_BYTES = 1024 * 1024
STORAGE_BASE_DIR = "stored_contacts"

st.set_page_config(
    page_title="Comparative Workspace & Collective Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if "contacts" not in st.session_state:
    st.session_state.contacts = ["Raj"]
if "selected_contact" not in st.session_state:
    st.session_state.selected_contact = "Raj"
if "collective_selected" not in st.session_state:
    st.session_state.collective_selected = ["Raj"]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

def check_connection(url="https://httpbin.org/status/200"):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def get_contact_folder(contact_name: str) -> str:
    path = os.path.join(STORAGE_BASE_DIR, contact_name)
    os.makedirs(path, exist_ok=True)
    return path

def save_uploaded_file_chunked(uploaded_file, target_dir: str):
    file_size_mb = uploaded_file.size / (1024 * 1024)
    filename = uploaded_file.name

    if file_size_mb > STREAMLIT_MAX_FILE_SIZE_MB:
        st.error(f"Limit Exceeded: `{filename}` is {file_size_mb:.2f} MB.")
        return False

    dest_path = os.path.join(target_dir, filename)
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        uploaded_file.seek(0)
        total_bytes = uploaded_file.size
        bytes_written = 0

        with open(dest_path, "wb") as f:
            while True:
                chunk = uploaded_file.read(CHUNK_SIZE_BYTES)
                if not chunk:
                    break
                f.write(chunk)
                bytes_written += len(chunk)
                progress = min(int((bytes_written / total_bytes) * 100), 100)
                progress_bar.progress(progress)
                status_text.text(f"Writing {filename}: {progress}%")

        progress_bar.empty()
        status_text.empty()

        if filename.lower().endswith(".zip"):
            extract_status = st.info(f"Extracting `{filename}`...")
            try:
                with zipfile.ZipFile(dest_path, "r") as zip_ref:
                    zip_ref.extractall(target_dir)
                os.remove(dest_path)
                extract_status.empty()
                st.success(f"Extracted `{filename}` successfully.")
            except zipfile.BadZipFile:
                extract_status.empty()
                st.error(f"Corruption Error: `{filename}` is not a valid ZIP.")
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                return False
        else:
            st.success(f"Saved `{filename}` to persistent storage.")
        return True

    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Processing Error: {str(e)}")
        return False

# Sidebar: Contacts & Persistent Connection Status
with st.sidebar:
    st.header("System Status")
    is_connected = check_connection()
    if is_connected:
        st.success("☁️ Cloud Connection: Online", icon="✅")
    else:
        st.error("⚠️ Cloud Connection: Interrupted", icon="❌")

    st.markdown("---")
    st.header("Contacts")
    selected = st.radio(
        "Select Workspace:",
        options=st.session_state.contacts,
        index=st.session_state.contacts.index(st.session_state.selected_contact) if st.session_state.selected_contact in st.session_state.contacts else 0
    )
    st.session_state.selected_contact = selected

    st.markdown("---")
    new_contact = st.text_input("Add New Contact:")
    if st.button("Add Contact"):
        clean_name = new_contact.strip()
        if clean_name and clean_name not in st.session_state.contacts:
            st.session_state.contacts.append(clean_name)
            get_contact_folder(clean_name)
            st.rerun()

# Split Layout
col_collective, col_workspace = st.columns([1, 1], gap="large")

# Left Column: Collective Workspace
with col_collective:
    st.markdown("## 🌐 Collective Workspace")
    st.session_state.collective_selected = st.multiselect(
        "Contacts to analyze simultaneously:",
        options=st.session_state.contacts,
        default=[c for c in st.session_state.collective_selected if c in st.session_state.contacts]
    )
    collective_prompt = st.text_area("Collective Analysis Prompt:", height=140)

    if st.button("Run Multi-Contact Analysis"):
        if not st.session_state.collective_selected or not collective_prompt.strip():
            st.error("Select contacts and enter a prompt.")
        else:
            st.info("Aggregating workspace files for analysis...")

# Right Column: Dedicated Workspace
with col_workspace:
    active_contact = st.session_state.selected_contact
    contact_dir = get_contact_folder(active_contact)

    st.markdown(f"## 👤 Workspace: {active_contact}")
    uploaded_files = st.file_uploader(
        f"Upload files for {active_contact}",
        type=["zip", "txt", "jpg", "png", "mp4", "opus", "oga"],
        accept_multiple_files=True,
        key=f"uploader_{active_contact}"
    )

    if uploaded_files:
        upload_success_flag = False
        for up_file in uploaded_files:
            file_path = os.path.join(contact_dir, up_file.name)
            if not os.path.exists(file_path):
                if save_uploaded_file_chunked(up_file, contact_dir):
                    upload_success_flag = True
        if upload_success_flag:
            st.rerun()

    stored_files = [f for f in os.listdir(contact_dir) if os.path.isfile(os.path.join(contact_dir, f))]
    with st.expander(f"📁 Stored Files ({len(stored_files)})"):
        for sf in stored_files:
            c_name, c_del = st.columns([4, 1])
            c_name.text(f"• {sf}")
            if c_del.button("Delete", key=f"del_{active_contact}_{sf}"):
                os.remove(os.path.join(contact_dir, sf))
                st.rerun()

    st.markdown("---")
    st.markdown(f"### 💬 Interaction: {active_contact}")
    
    # Text Input
    sim_prompt = st.text_area("Input prompt for text reply:", height=100)
    if st.button(f"Send Text to {active_contact}") and sim_prompt.strip():
        if active_contact not in st.session_state.chat_history:
            st.session_state.chat_history[active_contact] = []
        response_text = f"Simulated response for {active_contact} referencing {len(stored_files)} files."
        st.session_state.chat_history[active_contact].append({"role": "user", "text": sim_prompt})
        st.session_state.chat_history[active_contact].append({"role": "assistant", "text": response_text})

    # Voice Input
    voice_input = st.audio_input("Record voice prompt:")
    if voice_input:
        if active_contact not in st.session_state.chat_history:
            st.session_state.chat_history[active_contact] = []
        voice_response = f"Processed voice input for {active_contact}."
        st.session_state.chat_history[active_contact].append({"role": "user", "text": "[Audio Prompt]"})
        st.session_state.chat_history[active_contact].append({"role": "assistant", "text": voice_response})

    # Render Chat History with Audio Output capability
    if active_contact in st.session_state.chat_history:
        for msg_idx, msg in enumerate(reversed(st.session_state.chat_history[active_contact])):
            prefix = "User" if msg["role"] == "user" else active_contact
            st.write(f"**{prefix}:** {msg['text']}")
            
            if msg["role"] == "assistant":
                tts_buffer = io.BytesIO()
                tts = gTTS(text=msg['text'], lang='en')
                tts.write_to_fp(tts_buffer)
                tts_buffer.seek(0)
                st.audio(tts_buffer, format='audio/mp3', key=f"audio_{active_contact}_{msg_idx}")
