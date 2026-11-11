import streamlit as st
import zipfile
import os
from google.generativeai import configure, GenerativeModel

st.set_page_config(layout="wide", page_title="Folder-based Chat Analyzer")

# --- UI Customization for WhatsApp Theme ---
def apply_whatsapp_theme():
    st.markdown("""
        <style>
        /* Main background and sidebar */
        [data-testid="stAppViewContainer"] {
            background-color: #ECE5DD;
        }
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
        }
        
        /* Headers and accents */
        h1, h2, h3, .stSubheader {
            color: #075E54 !important;
        }
        
        /* Sidebar styling */
        .css-170z1fq, [data-testid="stSidebar"] {
            border-right: 2px solid #25D366;
        }
        
        /* Chat bubbles */
        .stChatMessage {
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
        [data-testid="stChatMessageUser"] {
            background-color: #DCF8C6 !important;
            border: 1px solid #25D366;
        }
        [data-testid="stChatMessageUser"] .stMarkdown {
            color: black !important;
        }
        [data-testid="stChatMessageAssistant"] {
            background-color: #FFFFFF !important;
        }
        
        /* Buttons */
        div.stButton > button {
            background-color: #25D366 !important;
            color: white !important;
            border-radius: 20px;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #128C7E !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_whatsapp_theme()

# --- Base Directory Setup ---
BASE_DIR = "user_folders"
KEY_FILE = "api_key.txt"

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# --- API Key Management ---
api_key = ""
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        api_key = f.read().strip()

st.sidebar.title("Chat Manager")

if not api_key:
    user_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
    if st.sidebar.button("Save API Key"):
        if user_key:
            with open(KEY_FILE, "w") as f:
                f.write(user_key)
            st.rerun()
else:
    st.sidebar.success("API Key is active.")
    if st.sidebar.button("Remove API Key"):
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("Folder Management")

# --- Create New Folder ---
new_folder_name = st.sidebar.text_input("Create New Folder:")
if st.sidebar.button("Create Folder") and new_folder_name:
    safe_name = "".join([c for c in new_folder_name if c.isalpha() or c.isdigit() or c in ' -_']).rstrip()
    if safe_name:
        target_path = os.path.join(BASE_DIR, safe_name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
            st.rerun()

# --- Select Folder ---
folders = [f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))]
selected_folder = st.sidebar.radio("Select Folder:", folders if folders else ["No folders available"])

# --- Main Interface Logic ---
if selected_folder != "No folders available":
    current_folder_path = os.path.join(BASE_DIR, selected_folder)
    st.title(f"Active Chat: {selected_folder}")
    
    st.sidebar.divider()
    st.sidebar.subheader(f"Upload Data for {selected_folder}")
    uploaded_zip = st.sidebar.file_uploader("Select ZIP file", type=["zip"], key=selected_folder)
    
    if uploaded_zip is not None:
        flag_file = os.path.join(current_folder_path, f".processed_{uploaded_zip.name}")
        if not os.path.exists(flag_file):
            with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
                zip_ref.extractall(current_folder_path)
            with open(flag_file, "w") as f:
                f.write("processed")
            st.sidebar.success("✅ File successfully extracted and merged!")

    # --- Aggregate Folder Data ---
    folder_texts = []
    video_count = 0
    audio_count = 0
    image_count = 0
    
    for root, dirs, files in os.walk(current_folder_path):
        for file in files:
            if file.endswith(".txt"):
                with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                    folder_texts.append(f.read())
            elif file.endswith(('.jpg', '.png', '.jpeg')):
                image_count += 1
            elif file.endswith(('.mp4', '.avi', '.mov')):
                video_count += 1
            elif file.endswith(('.mp3', '.wav', '.opus')):
                audio_count += 1

    full_context = "\n---\n".join(folder_texts)

    # --- Chat Session Management ---
    session_key = f"messages_{selected_folder}"
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    for msg in st.session_state[session_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask something about this chat context..."):
        st.session_state[session_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if api_key and full_context:
            try:
                configure(api_key=api_key)
                model = GenerativeModel('gemini-1.5-flash')
                response_prompt = f"You are the AI assistant analyzing this specific chat folder.\n\nContext Data:\n{full_context}\n\nQuestion: {prompt}"
                response = model.generate_content(response_prompt)
                ai_reply = response.text
            except Exception as e:
                ai_reply = f"Cloud Service Error: {e}"
        elif not full_context:
            ai_reply = "No readable text files (txt) found in this folder. Please upload a WhatsApp export ZIP file."
        else:
            ai_reply = "API configuration is invalid or missing."

        st.session_state[session_key].append({"role": "ai", "content": ai_reply})
        with st.chat_message("ai"):
            st.markdown(ai_reply)
            
        st.info(f"📁 Context loaded with {image_count} images, {audio_count} audio files, and {video_count} videos.")
else:
    st.title("Welcome")
    st.info("Please create a new folder from the sidebar to begin.")
