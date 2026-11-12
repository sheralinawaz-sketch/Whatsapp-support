import os
import shutil
import zipfile
import streamlit as st

# Platform Limits & Configuration Constants
STREAMLIT_MAX_FILE_SIZE_MB = 200  # Default server maxUploadSize in Streamlit config
CHUNK_SIZE_BYTES = 1024 * 1024    # 1MB chunk size for controlled buffer writing
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

def get_contact_folder(contact_name: str) -> str:
    path = os.path.join(STORAGE_BASE_DIR, contact_name)
    os.makedirs(path, exist_ok=True)
    return path

def save_uploaded_file_chunked(uploaded_file, target_dir: str):
    file_size_mb = uploaded_file.size / (1024 * 1024)
    filename = uploaded_file.name

    if file_size_mb > STREAMLIT_MAX_FILE_SIZE_MB:
        st.error(
            f"Limit Exceeded: `{filename}` is {file_size_mb:.2f} MB. "
            f"Streamlit Community Cloud allows up to {STREAMLIT_MAX_FILE_SIZE_MB} MB per file."
        )
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
                status_text.text(f"Writing {filename}: {progress}% ({bytes_written / (1024*1024):.1f}/{file_size_mb:.1f} MB)")

        progress_bar.empty()
        status_text.empty()

        # Handle zip extraction automatically if archive uploaded
        if filename.lower().endswith(".zip"):
            extract_status = st.info(f"Extracting archive `{filename}`...")
            try:
                with zipfile.ZipFile(dest_path, "r") as zip_ref:
                    zip_ref.extractall(target_dir)
                os.remove(dest_path)
                extract_status.empty()
                st.success(f"Extracted and saved contents of `{filename}` successfully.")
            except zipfile.BadZipFile:
                extract_status.empty()
                st.error(f"Corruption Error: `{filename}` is not a valid or complete ZIP archive.")
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                return False
        else:
            st.success(f"Saved `{filename}` ({file_size_mb:.2f} MB) to persistent storage.")

        return True

    except PermissionError:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Filesystem Error: Insufficient permissions to write `{filename}` to storage.")
        return False
    except OSError as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Storage Exhaustion/OS Error: {str(e)}. Free platform disk space may be depleted.")
        return False
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Processing Error on `{filename}`: {type(e).__name__} - {str(e)}")
        return False

# Sidebar: Contacts Navigation & Management
with st.sidebar:
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
        elif clean_name in st.session_state.contacts:
            st.warning(f"Contact '{clean_name}' already exists.")

# Split Layout
col_collective, col_workspace = st.columns([1, 1], gap="large")

# Left Column: Collective Workspace
with col_collective:
    st.markdown("## 🌐 Collective Workspace")
    st.caption("Cross-contact queries and global intelligence")

    st.session_state.collective_selected = st.multiselect(
        "Contacts to analyze simultaneously:",
        options=st.session_state.contacts,
        default=[c for c in st.session_state.collective_selected if c in st.session_state.contacts]
    )

    collective_prompt = st.text_area(
        "Collective Analysis Prompt:",
        placeholder="Identify common themes across selected contacts...",
        height=140
    )

    if st.button("Run Multi-Contact Analysis"):
        if not st.session_state.collective_selected:
            st.error("Platform Error: Select at least one contact for collective analysis.")
        elif not collective_prompt.strip():
            st.error("Platform Error: Prompt cannot be empty.")
        else:
            total_files = 0
            for c in st.session_state.collective_selected:
                folder = get_contact_folder(c)
                total_files += len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
            st.info(f"Analyzing {len(st.session_state.collective_selected)} contacts ({total_files} stored files aggregated)...")

# Right Column: Dedicated Workspace
with col_workspace:
    active_contact = st.session_state.selected_contact
    contact_dir = get_contact_folder(active_contact)

    st.markdown(f"## 👤 Workspace: {active_contact}")
    st.caption("Persistent local storage—operates independently of network state.")

    st.markdown(f"**Upload WhatsApp export files for {active_contact}**")
    uploaded_files = st.file_uploader(
        f"Upload files for {active_contact}",
        type=["zip", "txt", "jpg", "png", "mp4", "opus", "oga"],
        accept_multiple_files=True,
        key=f"uploader_{active_contact}",
        label_visibility="collapsed"
    )

    if uploaded_files:
        upload_success_flag = False
        for up_file in uploaded_files:
            file_path = os.path.join(contact_dir, up_file.name)
            # Avoid re-saving files that already exist identically
            if not os.path.exists(file_path):
                if save_uploaded_file_chunked(up_file, contact_dir):
                    upload_success_flag = True
        if upload_success_flag:
            st.rerun()

    st.caption(f"Max payload: {STREAMLIT_MAX_FILE_SIZE_MB}MB per file • ZIP, TXT, JPG, PNG, MP4, OPUS, OGA")

    # Stored Files Display
    stored_files = [f for f in os.listdir(contact_dir) if os.path.isfile(os.path.join(contact_dir, f))]
    with st.expander(f"📁 Stored Files for {active_contact} ({len(stored_files)})", expanded=False):
        if stored_files:
            for sf in stored_files:
                f_size_kb = os.path.getsize(os.path.join(contact_dir, sf)) / 1024
                c_name, c_del = st.columns([4, 1])
                c_name.text(f"• {sf} ({f_size_kb:.1f} KB)")
                if c_del.button("Delete", key=f"del_{active_contact}_{sf}"):
                    os.remove(os.path.join(contact_dir, sf))
                    st.rerun()
        else:
            st.write("No files stored yet.")

    st.markdown("---")
    st.markdown(f"### 💬 Simulated Interaction: {active_contact}")
    sim_prompt = st.text_area(f"Input prompt for {active_contact}:", height=100, key=f"sim_input_{active_contact}")

    if st.button(f"Send to {active_contact}"):
        if not sim_prompt.strip():
            st.error("Input Error: Prompt cannot be empty.")
        else:
            if active_contact not in st.session_state.chat_history:
                st.session_state.chat_history[active_contact] = []
            st.session_state.chat_history[active_contact].append({"role": "user", "text": sim_prompt})
            st.session_state.chat_history[active_contact].append(
                {"role": "assistant", "text": f"Simulated response referencing {len(stored_files)} files in {active_contact}'s storage."}
            )

    # Render Chat History
    if active_contact in st.session_state.chat_history:
        for msg in reversed(st.session_state.chat_history[active_contact]):
            prefix = "User" if msg["role"] == "user" else active_contact
            st.write(f"**{prefix}:** {msg['text']}")
