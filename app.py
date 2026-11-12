import streamlit as st

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

st.header(f"Dedicated Workspace: {selected_contacts[0] if selected_contacts else 'Contact'}")

uploaded_files = st.file_uploader(
    "Upload WhatsApp Export files",
    type=["zip", "txt", "jpg", "png", "mp4", "opus", "mp3", "wav", "mov", "avi", "mkv"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"Total files uploaded: {len(uploaded_files)}")
    
    text_files = [f for f in uploaded_files if f.name.endswith('.txt')]
    media_files = [f for f in uploaded_files if not f.name.endswith('.txt')]
    
    cols = st.columns(3)
    cols[0]. metric("Text Files", len(text_files))
    cols[1].metric("Media Files", len(media_files))
    cols[2].metric("Total Processed", len(uploaded_files))
    
    for file in uploaded_files:
        st.write(f"processing: {file.name}")
