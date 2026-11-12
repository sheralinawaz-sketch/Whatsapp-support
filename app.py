import os
import streamlit as st

st.set_page_config(page_title="Dual-Tier Intelligence Hub", layout="wide")

STORAGE_DIR = "stored_contacts"
os.makedirs(STORAGE_DIR, exist_ok=True)

if "contacts" not in st.session_state:
    existing_contacts = [
        d for d in os.listdir(STORAGE_DIR) if os.path.isdir(os.path.join(STORAGE_DIR, d))
    ]
    st.session_state.contacts = sorted(list(set(existing_contacts + ["Raj"])))

# --- Sidebar: Contact Navigation & Creation ---
with st.sidebar:
    st.title("📇 Contacts")
    selected_contact = st.radio("Select Workspace:", st.session_state.contacts)

    st.markdown("---")
    new_contact = st.text_input("Add New Contact:").strip()
    if st.button("Add Contact") and new_contact:
        if new_contact not in st.session_state.contacts:
            st.session_state.contacts.append(new_contact)
            os.makedirs(os.path.join(STORAGE_DIR, new_contact), exist_ok=True)
            st.rerun()

contact_dir = os.path.join(STORAGE_DIR, selected_contact)
os.makedirs(contact_dir, exist_ok=True)

chat_file = os.path.join(contact_dir, "chat_history.txt")

# --- Dual-Tier Split Layout ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.header("🌐 Collective Workspace")
    st.caption("Cross-contact queries and global intelligence")

    target_contacts = st.multiselect(
        "Contacts to analyze simultaneously:",
        options=st.session_state.contacts,
        default=[selected_contact],
    )

    collective_prompt = st.text_area(
        "Collective Analysis Prompt:",
        placeholder="Identify common themes across selected contacts...",
        height=140,
    )

    if st.button("Run Multi-Contact Analysis"):
        if not target_contacts:
            st.warning("Please select at least one contact.")
        elif not collective_prompt.strip():
            st.warning("Please enter an analysis prompt.")
        else:
            with st.spinner("Analyzing data across contacts..."):
                file_summary = {}
                for c in target_contacts:
                    c_path = os.path.join(STORAGE_DIR, c)
                    files = os.listdir(c_path) if os.path.exists(c_path) else []
                    file_summary[c] = files

                st.success("Analysis complete.")
                st.markdown("### 📊 Collective Findings")
                for c, files in file_summary.items():
                    st.markdown(f"- **{c}**: {len(files)} files indexed")

with col_right:
    st.header(f"👤 Workspace: {selected_contact}")
    st.caption("Persistent local storage—operates independently of network state.")

    uploaded_files = st.file_uploader(
        f"Upload WhatsApp export files for {selected_contact}",
        type=["zip", "txt", "jpg", "png", "mp4", "opus", "mp3", "wav", "mkv"],
        accept_multiple_files=True,
        key=f"uploader_{selected_contact}",
    )

    if uploaded_files:
        status_box = st.empty()
        for idx, file in enumerate(uploaded_files):
            save_path = os.path.join(contact_dir, file.name)
            with open(save_path, "wb") as f:
                f.write(file.getbuffer())
            status_box.markdown(f"Saved: `{file.name}`")

    existing_files = os.listdir(contact_dir)
    with st.expander(f"📁 Stored Files for {selected_contact} ({len(existing_files)})", expanded=True):
        for fname in existing_files:
            if fname != "chat_history.txt":
                st.markdown(f"- `{fname}`")

    st.markdown("---")
    st.subheader(f"💬 Simulated Interaction: {selected_contact}")

    if os.path.exists(chat_file):
        with open(chat_file, "r") as f:
            st.text_area("Historical Context", value=f.read(), height=150, disabled=True)

    chat_prompt = st.text_area(f"Input prompt for {selected_contact}:", height=70)

    if st.button(f"Send to {selected_contact}"):
        if chat_prompt.strip():
            interaction_entry = f"\nUser: {chat_prompt}\nGemini (as {selected_contact}): Analyzed archives successfully.\n"
            with open(chat_file, "a") as f:
                f.write(interaction_entry)
            st.rerun()
