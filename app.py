import streamlit as st
import zipfile
import os
from google.generativeai import configure, GenerativeModel

st.set_page_config(layout="wide", page_title="WhatsApp AI Chat")

# --- فولڈرز اور فائل کی سیٹنگ ---
DATA_DIR = "saved_chats"
KEY_FILE = "api_key.txt"

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# --- API Key محفوظ کرنے کا نظام ---
api_key = ""
# اگر فائل میں پہلے سے Key موجود ہے، تو اسے پڑھیں
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        api_key = f.read().strip()

st.sidebar.title("سیٹنگز اور ڈیٹا")

# اگر API Key موجود نہیں ہے، تو یوزر سے مانگیں
if not api_key:
    user_key = st.sidebar.text_input("Gemini API Key درج کریں:", type="password")
    if st.sidebar.button("API Key محفوظ کریں"):
        if user_key:
            with open(KEY_FILE, "w") as f:
                f.write(user_key)
            st.sidebar.success("✅ API Key ہمیشہ کے لیے محفوظ ہو گئی!")
            st.rerun() # پیج کو ریفریش کرنے کے لیے تاکہ Key لوڈ ہو جائے
        else:
            st.sidebar.error("براہ کرم پہلے API Key درج کریں۔")
else:
    st.sidebar.success("✅ API Key سسٹم میں محفوظ ہے۔")
    if st.sidebar.button("API Key تبدیل کریں / ہٹائیں"):
        if os.path.exists(KEY_FILE):
            os.remove(KEY_FILE)
        st.rerun()

st.sidebar.divider()
st.sidebar.subheader("چیٹ اپڈیٹ کریں")

# ZIP فائل اپلوڈر
uploaded_zip = st.sidebar.file_uploader("واٹس ایپ کی ایکسپورٹ کی گئی ZIP فائل اپلوڈ کریں", type=["zip"])

if uploaded_zip is not None:
    # اس بات کو یقینی بنانا کہ بار بار ریفریش پر ایک ہی فائل دوبارہ ایکسٹریکٹ نہ ہو
    if 'last_uploaded' not in st.session_state or st.session_state.last_uploaded != uploaded_zip.name:
        with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
            # پرانی فائلز کو ہٹا کر نئی فائلز ایکسٹریکٹ کرے گا
            zip_ref.extractall(DATA_DIR)
        st.session_state.last_uploaded = uploaded_zip.name
        st.sidebar.success("✅ چیٹ ڈیٹا محفوظ ہو گیا! اب ریفریش کرنے پر بھی غائب نہیں ہوگا۔")

# --- محفوظ شدہ ڈیٹا کو پڑھنا ---
chat_text = ""
media_files_count = 0

if os.path.exists(DATA_DIR):
    for file in os.listdir(DATA_DIR):
        if file.endswith(".txt"):
            with open(os.path.join(DATA_DIR, file), "r", encoding="utf-8") as f:
                chat_text = f.read()
        elif file.endswith(('.jpg', '.png', '.jpeg', '.mp4', '.mp3', '.opus', '.wav')):
            media_files_count += 1

# --- مین ایپ انٹرفیس ---
st.title("WhatsApp Chat Analyzer 🤖")

if api_key:
    try:
        configure(api_key=api_key)
        # جیمنی ماڈل سیٹ کر رہے ہیں
        model = GenerativeModel('gemini-1.5-flash')
        
        if chat_text:
            st.info(f"📂 محفوظ کی گئی واٹس ایپ چیٹ لوڈ ہو چکی ہے۔ (ساتھ میں {media_files_count} میڈیا فائلز بھی موجود ہیں)")
            
            # چیٹ ہسٹری کو سیشن میں محفوظ رکھنا تاکہ سکرین پر نظر آئے
            if "messages" not in st.session_state:
                st.session_state.messages = []
                
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
