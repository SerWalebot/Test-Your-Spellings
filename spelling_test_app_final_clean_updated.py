
import streamlit as st

# Disable spellcheck in text inputs
st.markdown("""
    <style>
    textarea, input[type="text"] {
        spellcheck: false;
    }
    </style>
""", unsafe_allow_html=True)
import random
import time
from gtts import gTTS
import base64
import pandas as pd
from datetime import datetime, timedelta

# Constants
WORDS = ["accommodate", "acknowledgment", "conscience", "conscientious", "embarrass",
         "exhilarate", "harass", "millennium", "noticeable", "playwright",
         "rhythm", "supersede", "threshold", "twelfth", "weird"]
TEST_DURATION = 180  # 3 minutes
ATTEMPT_LIMIT = 2
ATTEMPT_WINDOW = timedelta(hours=1)
ADMIN_PASSWORD = "admin123"
LOG_FILE = "attempt_log.csv"

# Load or initialize attempt log
try:
    log_df = pd.read_csv(LOG_FILE)
except FileNotFoundError:
    log_df = pd.DataFrame(columns=["Name", "Score", "TimeTaken", "Timestamp", "Incorrect"])

# Helper functions
def generate_audio(word):
    tts = gTTS(word)
    tts.save("word.mp3")
    with open("word.mp3", "rb") as f:
        audio_bytes = f.read()
    return audio_bytes

def get_random_words(n=10):
    return random.sample(WORDS, n)

def get_attempts(name):
    now = datetime.now()
    recent_attempts = log_df[(log_df["Name"] == name) & 
                             (pd.to_datetime(log_df["Timestamp"]) > now - ATTEMPT_WINDOW)]
    return len(recent_attempts)

def save_attempt(name, score, time_taken, incorrect):
    global log_df
    new_entry = {
        "Name": name,
        "Score": score,
        "TimeTaken": time_taken,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Incorrect": "; ".join([f"{w}→{u}" for w, u in incorrect])
    }
    log_df = pd.concat([log_df, pd.DataFrame([new_entry])], ignore_index=True)
    log_df.to_csv(LOG_FILE, index=False)

def display_feedback(score):
    if score >= 8:
        st.success("🎉 Excellent work! You're a spelling star!")
    elif score >= 5:
        st.info("🙂 Good effort! Keep practicing!")
    else:
        st.warning("😢 Don't worry, try again and you'll improve!")

# UI
st.set_page_config(page_title="Spelling Test", layout="centered")
st.markdown("<h1 style='text-align: center; color: navy;'>📝 Spelling Test</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📝 Take Test", "🔐 Admin Dashboard"])

with tab1:
    name = st.text_input("Enter your name:", key="name_input")
    if name:
        attempts = get_attempts(name)
        if attempts >= ATTEMPT_LIMIT:
            st.error("⏳ You've reached the maximum of 2 attempts per hour. Please try again later.")
        else:
            if "start_time" not in st.session_state:
                st.session_state.start_time = time.time()
                st.session_state.words = get_random_words()
                st.session_state.answers = {}
                st.session_state.submitted = False

            elapsed = int(time.time() - st.session_state.start_time)
            remaining = TEST_DURATION - elapsed
            if remaining <= 0:
                st.warning("⏰ Time's up!")
                st.session_state.submitted = True

            if not st.session_state.submitted:
                st.info(f"⏱️ Time remaining: {remaining} seconds")
                for i, word in enumerate(st.session_state.words):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button(f"🔊 Hear Word {i+1}", key=f"play_{i}"):
                            st.audio(generate_audio(word), format="audio/mp3")
                    with col2:
                        st.session_state.answers[word] = st.text_input(f"Spell word {i+1}:", key=f"input_{i}", disabled=st.session_state.submitted, 
                                                                       placeholder="Type your spelling here...", 
                                                                       label_visibility="collapsed")

                if st.button("✅ Submit", key="submit_btn"):
                    st.session_state.submitted = True
                    st.session_state.end_time = time.time()

            if st.session_state.submitted:
                correct = 0
                incorrect = []
                for word in st.session_state.words:
                    user_input = st.session_state.answers.get(word, "").strip().lower()
                    if user_input == word.lower():
                        correct += 1
                    else:
                        incorrect.append((word, user_input))
                time_taken = int(st.session_state.end_time - st.session_state.start_time)
                save_attempt(name, correct, time_taken, incorrect)

                st.success(f"✅ You scored {correct}/10 in {time_taken} seconds.")
                display_feedback(correct)

                if incorrect:
                    st.subheader("❌ Words you missed:")
                    for w, u in incorrect:
                        st.write(f"**{w}** → You typed: *{u}*")

with tab2:
    st.subheader("Admin Login")
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Access granted.")
        st.dataframe(log_df)

        with st.expander("📅 Filter by Date"):
            start_date = st.date_input("Start date", value=datetime.today())
            end_date = st.date_input("End date", value=datetime.today())
            filtered = log_df[
                (pd.to_datetime(log_df["Timestamp"]) >= pd.to_datetime(start_date)) &
                (pd.to_datetime(log_df["Timestamp"]) <= pd.to_datetime(end_date) + pd.Timedelta(days=1))
            ]
            st.dataframe(filtered)

        if st.button("📥 Download CSV"):
            csv = filtered.to_csv(index=False).encode()
            st.download_button("Download Filtered Results", csv, "filtered_results.csv", "text/csv")

        st.subheader("🏆 Leaderboard")
        leaderboard = log_df.sort_values(by=["Score", "TimeTaken"], ascending=[False, True])
        st.dataframe(leaderboard[["Name", "Score", "TimeTaken", "Timestamp"]])
    elif pwd:
        st.error("Incorrect password.")
