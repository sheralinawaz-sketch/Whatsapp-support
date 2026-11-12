import streamlit as st
import time

st.set_page_config(
    page_title="Dual-Tier Intelligence Workspace",
    layout="wide"
)

st.title("Dual-Tier Intelligence Workspace")
st.subheader("Shared Multi-Contact Analysis Hub")

with st.expander("Comparative Workspace & Collective Intelligence"):
    selected_contacts = st.multiselect(
        "Select Contacts for Collective Analysis:",
        ["Raj"],
        default=["Raj"]
    )
    collective_query = st.text_input("Collective Query / Cross-Analysis Prompt:")
    run_button = st.button("Run Multi-Analysis")

st.markdown("---")

contact_display = selected_contacts[0] if selected_contacts else "Contact"
st.header(f"Dedicated Workspace: {contact_display}")

uploaded_files = st.file_uploader(
    "Upload WhatsApp Export files",
    type=["zip", "txt", "jpg", "png", "mp4", "opus", "mp3", "wav", "mov", "avi", "mkv", "oga"],
    accept_multiple_files=True
)

if uploaded_files:
    total_count = len(uploaded_files)
    st.info(f"Total files detected: {total_count}")

    text_files = [f for f in uploaded_files if f.name.endswith(".txt")]
    media_files = [f for f in uploaded_files if not f.name.endswith(".txt")]

    cols = st.columns(3)
    cols[0].metric("Text Files", len(text_files))
    cols[1].metric("Media Files", len(media_files))
    cols[2].metric("Total Processed", total_count)

    progress_bar = st.progress(0, text="Initializing processing...")
    status_text = st.empty()

    for idx, file in enumerate(uploaded_files):
        percent_complete = int(((idx + 1) / total_count) * 100)
        status_text.markdown(f"**Processing ({idx + 1}/{total_count}):** `{file.name}` ({file.size / 1024:.1f} KB)")
        
        _ = file.read()
        file.seek(0)
        
        progress_bar.progress(percent_complete, text=f"Processing file {idx + 1} of {total_count}")
        time.sleep(0.05)

    status_text.success(f"Processing complete: All {total_count} files successfully loaded.")
