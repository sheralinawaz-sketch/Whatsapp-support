import streamlit as st
import zipfile
import os
import shutil
from google.generativeai import configure, GenerativeModel

st.set_page_config(layout="wide", page_title="Intelligence Playground & Workspace")

# --- UI Customization: Modern Dark Theme & Custom CSS ---
st.markdown("""
    <style>
    /* Global Base */
    [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Headers & Typography */
    h1, h2, h3, h4, .stSubheader {
        color: #58a6ff !important;
        font-weight: 600;
    }
    
    /* Metrics Cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .metric-title {
        color: #8b949e;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #f0f6fc;
        font-size: 1.3rem;
        font-weight: 700;
    }

    /* Workspace Containers */
    .workspace-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }

    /* Chat Messages */
    .stChatMessage {
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    [data-testid="stChatMessageUser"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151;
    }
    [data-testid="stChatMessageAssistant"] {
        background-color: #111827 !important;
        border: 1px solid #1f2937;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border: 1px solid rgba(240, 246, 252, 0.1);
        border-radius: 6px;
        font-weight: 500;
        transition: 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #2ea043 !important;
        border-color: #8b949e;
    }
    </style>
""", unsafe_allow_html=True)

# --- Base Directory Architecture ---
BASE_DIR = "contacts_data"
KEY_FILE = "gemini_key.txt"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

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
    st.sidebar.caption("API Key Loaded")
    if st.sidebar.button("Reset Key"):
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        st.rerun()

st.sidebar.divider()

# --- Contact Directory Operations ---
st.sidebar.subheader("Contact Manager")
new_contact = st.sidebar.text_input("Add Contact Folder:")
if st.sidebar.button("Create Contact") and new_contact:
    sanitized = "".join([c for c in new_contact if c.isalnum() or c in ' -_']).strip()
    if sanitized:
        c_path = os.path.join(BASE_DIR, sanitized)
        os.makedirs(os.path.join(c_path, "Text"), exist_ok=True)
        os.makedirs(os.path.join(c_path, "Media"), exist_ok=True)
        os.makedirs(os.path.join(c_path, "Audio"), exist_ok=True)
        st.rerun()

def get_contacts():
    return sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])

def extract_and_organize_zip(zip_file, contact_name):
    target_dir = os.path.join(BASE_DIR, contact_name)
    temp_dir = os.path.join(target_dir, "_tmp_extract")
    os.makedirs(temp_dir, exist_ok=True)

    text_dir = os.path.join(target_dir, "Text")
    media_dir = os.path.join(target_dir, "Media")
    audio_dir = os.path.join(target_dir, "Audio")

    os.makedirs(text_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    media_exts = ('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv', '.webp')
    audio_exts = ('.mp3', '.wav', '.opus', '.m4a', '.ogg', '.aac')
    text_exts = ('.txt', '.csv', '.json', '.log')

    for root, _, files in os.walk(temp_dir):
        for f in files:
            source = os.path.join(root, f)
            dest = None
            f_lower = f.lower()

            if f_lower.endswith(media_exts):
                dest = os.path.join(media_dir, f)
            elif f_lower.endswith(audio_exts):
                dest = os.path.join(audio_dir, f)
            elif f_lower.endswith(text_exts):
                dest = os.path.join(text_dir, f)
            
            if dest:
                shutil.move(source, dest)

    shutil.rmtree(temp_dir)

def get_folder_metrics(contact_name):
    c_path = os.path.join(BASE_DIR, contact_name)
    text_count = len(os.listdir(os.path.join(c_path, "Text"))) if os.path.exists(os.path.join(c_path, "Text")) else 0
    media_count = len(os.listdir(os.path.join(c_path, "Media"))) if os.path.exists(os.path.join(c_path, "Media")) else 0
    audio_count = len(os.listdir(os.path.join(c_path, "Audio"))) if os.path.exists(os.path.join(c_path, "Audio")) else 0
    return text_count, media_count, audio_count

def aggregate_context(contact_name):
    text_dir = os.path.join(BASE_DIR, contact_name, "Text")
    texts = []
    if os.path.exists(text_dir):
        for f in os.listdir(text_dir):
            if f.endswith('.txt'):
                with open(os.path.join(text_dir, f), 'r', encoding='utf-8', errors='ignore') as file:
                    texts.append(file.read())
    return "\n---\n".join(texts)

# --- Dual Contact Summary Engine (Sidebar) ---
contacts = get_contacts()

if len(contacts) >= 2:
    st.sidebar.subheader("Dual Summarizer Comparison")
    sum_c1 = st.sidebar.selectbox("Contact 1:", contacts, index=0, key="sum_c1")
    sum_c2 = st.sidebar.selectbox("Contact 2:", contacts, index=min(1, len(contacts)-1), key="sum_c2")

    if st.sidebar.button("Run Summaries"):
        if not api_key:
            st.sidebar.error("Gemini API key is required.")
        else:
            configure(api_key=api_key)
            model = GenerativeModel('gemini-1.5-flash')

            for target in [sum_c1, sum_c2]:
                context = aggregate_context(target)
                st.sidebar.markdown(f"**Analysis: {target}**")
                if context.strip():
                    try:
                        summary_res = model.generate_content(
                            f"Generate a clear, high-level intelligence summary of the following conversation logs:\n\n{context[:30000]}"
                        )
                        st.sidebar.info(summary_res.text)
                    except Exception as e:
                        st.sidebar.error(f"Error analyzing {target}: {e}")
                else:
                    st.sidebar.warning(f"No textual data in '{target}/Text'.")
                st.sidebar.divider()

# --- Main Layout: Dual-Workspace Playground ---
st.title("Dual-Workspace Intelligence Playground")

if not contacts:
    st.info("No contact folders available. Create contacts using the sidebar to begin.")
    st.stop()

col_left, col_right = st.columns(2)

def render_workspace_column(column_obj, workspace_key, default_index):
    with column_obj:
        st.markdown('<div class="workspace-card">', unsafe_allow_html=True)
        selected = st.selectbox(
            f"Select Contact ({workspace_key}):", 
            contacts, 
            index=min(default_index, len(contacts)-1),
            key=f"ws_select_{workspace_key}"
        )

        t_cnt, m_cnt, a_cnt = get_folder_metrics(selected)

        # Contact Metrics Display
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-card"><div class="metric-title">Text Docs</div><div class="metric-value">{t_cnt}</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-card"><div class="metric-title">Media Files</div><div class="metric-value">{m_cnt}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-card"><div class="metric-title">Audio Files</div><div class="metric-value">{a_cnt}</div></div>', unsafe_allow_html=True)

        # ZIP Upload & Auto-Sorting
        uploaded_zip = st.file_uploader(f"Upload ZIP to {selected}", type=["zip"], key=f"uploader_{workspace_key}_{selected}")
        if uploaded_zip is not None:
            flag_file = os.path.join(BASE_DIR, selected, f".processed_{uploaded_zip.name}")
            if not os.path.exists(flag_file):
                with st.spinner("Extracting & compartmentalizing assets..."):
                    extract_and_organize_zip(uploaded_zip, selected)
                    with open(flag_file, "w") as f:
                        f.write("processed")
                st.success("Extracted into Text/, Media/, and Audio/")
                st.rerun()

        # Dedicated Grounded Chat Interface
        st.subheader(f"Workspace Agent: {selected}")
        session_key = f"chat_history_{selected}"
        if session_key not in st.session_state:
            st.session_state[session_key] = []

        chat_container = st.container(height=380)
        for msg in st.session_state[session_key]:
            with chat_container.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_prompt = st.chat_input(f"Query {selected}'s context...", key=f"input_{workspace_key}")
        if user_prompt:
            st.session_state[session_key].append({"role": "user", "content": user_prompt})
            with chat_container.chat_message("user"):
                st.markdown(user_prompt)

            grounding_text = aggregate_context(selected)

            if api_key and grounding_text.strip():
                try:
                    configure(api_key=api_key)
                    model = GenerativeModel('gemini-1.5-flash')
                    full_prompt = (
                        f"You are an assistant analyzing records for contact: {selected}.\n"
                        f"Text Context:\n{grounding_text}\n\n"
                        f"User Request: {user_prompt}"
                    )
                    response = model.generate_content(full_prompt)
                    bot_reply = response.text
                except Exception as e:
                    bot_reply = f"Inference Error: {e}"
            elif not grounding_text.strip():
                bot_reply = f"No text records found in '{selected}/Text'. Upload a chat archive to query this workspace."
            else:
                bot_reply = "Gemini API key is missing. Set it in the sidebar."

            st.session_state[session_key].append({"role": "assistant", "content": bot_reply})
            with chat_container.chat_message("assistant"):
                st.markdown(bot_reply)

        st.markdown('</div>', unsafe_allow_html=True)

render_workspace_column(col_left, "Workspace A", 0)
render_workspace_column(col_right, "Workspace B", 1 if len(contacts) > 1 else 0)
