import streamlit as st
import random
import time
import csv
import io
from datetime import datetime
from gtts import gTTS
import base64

# Set page config at the top
st.set_page_config(page_title="Spelling Test", layout="centered")

# Disable spellcheck using custom CSS
st.markdown(
    '''
    <style>
    input[type="text"] {
        spellcheck: false;
    }
    </style>
    '''
, unsafe_allow_html=True)

# Sample word list
WORDS = [
    "accommodate", "acknowledge", "argument", "believe", "calendar",
    "category", "cemetery", "collectible", "column", "conscience",
    "conscious", "definitely", "discipline", "embarrass", "exceed",
    "existence", "foreign", "grateful", "guarantee", "harass"
]

# Admin password
ADMIN_PASSWORD = "admin123"

# Initialize session state
if 'word_list' not in st.session_state:
    st.session_state.word_list = random.sample(WORDS, 10)
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'end_time' not in st.session_state:
    st.session_state.end_time = None

# Title
st.title("📝 Spelling Test")

# User name input
user_name = st.text_input("Enter your name to begin:")

# Timer
DURATION = 120  # seconds
elapsed = int(time.time() - st.session_state.start_time)
remaining = max(0, DURATION - elapsed)
st.info(f"⏳ Time remaining: {remaining} seconds")

# Auto-submit if time is up
if remaining == 0 and not st.session_state.submitted:
    st.session_state.submitted = True
    st.session_state.end_time = time.time()
    st.warning("⏰ Time's up! Your test has been submitted automatically.")

# Spelling test form
if user_name and not st.session_state.submitted:
    with st.form("spelling_form"):
        for i, word in enumerate(st.session_state.word_list):
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.form_submit_button(f"🔊", key=f"audio_{i}"):
                    tts = gTTS(word)
                    fp = io.BytesIO()
                    tts.write_to_fp(fp)
                    fp.seek(0)
                    b64 = base64.b64encode(fp.read()).decode()
                    audio_html = f'''
                        <audio autoplay>
                        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                        </audio>
                    '''
                    st.markdown(audio_html, unsafe_allow_html=True)
            with col2:
                st.session_state.answers[word] = st.text_input(f"Word {i+1}", key=f"input_{i}")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.submitted = True
            st.session_state.end_time = time.time()

# Show results
if st.session_state.submitted:
    st.subheader("📊 Results")
    correct = 0
    for word in st.session_state.word_list:
        user_input = st.session_state.answers.get(word, "")
        if user_input.lower() == word.lower():
            st.success(f"✅ {word}")
            correct += 1
        else:
            st.error(f"❌ {user_input} (Correct: {word})")

    total = len(st.session_state.word_list)
    score = f"{correct}/{total}"
    time_taken = int(st.session_state.end_time - st.session_state.start_time)
    st.info(f"🧠 Score: {score}")
    st.info(f"⏱️ Time Taken: {time_taken} seconds")

    # Save to CSV
    result = {
        "Name": user_name,
        "Score": score,
        "Time Taken": time_taken,
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("results.csv", "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=result.keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(result)

# Admin dashboard
st.sidebar.title("🔐 Admin Login")
admin_pass = st.sidebar.text_input("Enter admin password:", type="password")
if admin_pass == ADMIN_PASSWORD:
    st.sidebar.success("Access granted")
    st.subheader("📋 Leaderboard")
    try:
        with open("results.csv", "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            if rows:
                st.table(rows)
                csv_data = io.StringIO()
                writer = csv.DictWriter(csv_data, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                st.download_button("📥 Download CSV", csv_data.getvalue(), "results.csv", "text/csv")
            else:
                st.info("No results yet.")
    except FileNotFoundError:
        st.info("No results file found.")