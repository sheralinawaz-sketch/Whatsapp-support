import streamlit as st
import google.generativeai as genai
import os
import tempfile

st.set_page_config(page_title="Multi-Media Summarizer", layout="centered")

st.title("🎙️💬 Multi-Media Audio/Video Summarizer")
st.write("Upload audio, video, or text to get summaries and draft replies.")

api_key = st.sidebar.text_input("Enter your Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    uploaded_file = st.file_uploader("Choose an audio or video file...", type=['mp3', 'wav', 'ogg', 'mp4', 'mov'])

    if uploaded_file is not None:
        if st.button("Analyze Media"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_file_path = temp_file.name

            with st.spinner("Analyzing audio/video with Gemini..."):
                try:
                    sample_file = genai.upload_file(path=temp_file_path)
                    prompt = "Analyze this media file. Provide a comprehensive summary in the language spoken, capturing key points."
                    response = model.generate_content([prompt, sample_file])
                    
                    summary = response.text
                    st.subheader("Analysis Summary:")
                    st.info(summary)
                    
                    st.session_state.messages.append({"role": "user", "content": f"Uploaded file: {uploaded_file.name}"})
                    st.session_state.messages.append({"role": "assistant", "content": summary})
                    
                    genai.delete_file(sample_file.name)
                    os.remove(temp_file_path)
                except Exception as e:
                    st.error(f"Error processing file: {e}")

    if user_input := st.chat_input("Type context or instructions for a reply..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            if 'model' in locals():
                with st.spinner("Drafting response..."):
                    try:
                        context_prompt = f"Based on our previous context, draft a response to this: {user_input}"
                        response = model.generate_content(context_prompt)
                        reply = response.text
                        st.markdown(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error generating reply: {e}")
            else:
                st.warning("Please enter your Gemini API Key in the sidebar to generate replies.")
else:
    st.info("Please enter your Gemini API Key in the sidebar to get started.")
