
import streamlit as st
import random
import time
import pandas as pd
from gtts import gTTS
import base64
from io import BytesIO
from datetime import datetime, timedelta

# ------------------ Configuration ------------------
st.set_page_config(page_title="Spelling Test", layout="centered")
BANNER_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/HD_transparent_picture.png/800px-HD_transparent_picture.png"  # Placeholder banner
ADMIN_PASSWORD = "admin123"
TEST_DURATION = 180  # 3 minutes
ATTEMPT_LIMIT = 2
ATTEMPT_WINDOW = timedelta(hours=1)
WORDS = ["accommodate", "acknowledgment", "conscientious", "entrepreneur", "pronunciation",
         "recommend", "rhythm", "supersede", "threshold", "vacuum", "maintenance", "liaison",
         "embarrass", "occasionally", "millennium", "harass", "definitely", "existence", "grateful", "independent"]

# ------------------ Helper Functions ------------------
def get_audio(word):
    tts = gTTS(word)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp

def load_log():
    try:
        return pd.read_csv("attempt_log.csv")
    except:
        return pd.DataFrame(columns=["Name", "Score", "Time Taken (s)", "Timestamp", "Incorrect Words"])

def save_log(df):
    df.to_csv("attempt_log.csv", index=False)

def get_attempts(df, name):
    now = datetime.now()
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    recent = df[(df["Name"] == name) & (now - df["Timestamp"] <= ATTEMPT_WINDOW)]
    return len(recent)

def display_feedback(score):
    if score >= 8:
        st.success("🎉 Excellent work! You're a spelling star!")
    elif score >= 5:
        st.info("🙂 Good effort! Keep practicing!")
    else:
        st.error("😢 Don't worry, try again and you'll improve!")

# ------------------ Main App ------------------
tab1, tab2 = st.tabs(["📝 Take Test", "🔐 Admin Dashboard"])

with tab1:
    st.image(BANNER_URL, use_column_width=True)
    st.title("Spelling Test")
    name = st.text_input("Enter your name:", key="name_input")

    if name:
        log_df = load_log()
        attempts = get_attempts(log_df, name)
        if attempts >= ATTEMPT_LIMIT:
            st.warning("⏳ You've reached the maximum of 2 attempts in the last hour.")
        else:
            if "start_time" not in st.session_state:
                st.session_state.start_time = time.time()
                st.session_state.words = random.sample(WORDS, 10)
                st.session_state.answers = {}
                st.session_state.submitted = False

            elapsed = int(time.time() - st.session_state.start_time)
            remaining = TEST_DURATION - elapsed
            if remaining <= 0:
                st.warning("⏰ Time's up!")
                st.session_state.submitted = True

            if not st.session_state.submitted:
                st.markdown(f"⏱️ **Time Remaining: {remaining} seconds**")
                for i, word in enumerate(st.session_state.words):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if st.button(f"🔊 Hear Word {i+1}", key=f"audio_{i}"):
                            st.audio(get_audio(word), format="audio/mp3")
                    with col2:
                        st.session_state.answers[word] = st.text_input(f"Spell word {i+1}:", key=f"word_{i}", disabled=st.session_state.submitted, help="Spellcheck is disabled", label_visibility="collapsed", placeholder="Type here...", spellcheck=False)

                if st.button("✅ Submit", key="submit_btn"):
                    st.session_state.submitted = True
                    st.session_state.end_time = time.time()

            if st.session_state.submitted:
                correct = 0
                incorrect_words = []
                for word in st.session_state.words:
                    user_input = st.session_state.answers.get(word, "").strip().lower()
                    if user_input == word.lower():
                        correct += 1
                    else:
                        incorrect_words.append(f"{word} (you typed: {user_input})")

                time_taken = int(st.session_state.end_time - st.session_state.start_time)
                st.subheader(f"Your Score: {correct}/10")
                st.write(f"⏱️ Time Taken: {time_taken} seconds")
                display_feedback(correct)

                if incorrect_words:
                    st.markdown("### ❌ Words You Missed:")
                    for item in incorrect_words:
                        st.write(f"- {item}")

                new_entry = pd.DataFrame([{
                    "Name": name,
                    "Score": correct,
                    "Time Taken (s)": time_taken,
                    "Timestamp": datetime.now(),
                    "Incorrect Words": "; ".join(incorrect_words)
                }])
                log_df = pd.concat([log_df, new_entry], ignore_index=True)
                save_log(log_df)

with tab2:
    st.title("Admin Dashboard")
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == ADMIN_PASSWORD:
        log_df = load_log()
        st.success("Access granted.")
        st.dataframe(log_df)

        with st.expander("📅 Filter by Date"):
            start_date = st.date_input("Start Date", value=datetime.now().date())
            end_date = st.date_input("End Date", value=datetime.now().date())
            mask = (pd.to_datetime(log_df["Timestamp"]).dt.date >= start_date) & (pd.to_datetime(log_df["Timestamp"]).dt.date <= end_date)
            filtered = log_df[mask]
            st.dataframe(filtered)

            csv = filtered.to_csv(index=False).encode()
            st.download_button("📥 Download Filtered CSV", csv, "filtered_attempts.csv", "text/csv")

        st.markdown("### 🏆 Leaderboard")
        leaderboard = log_df.sort_values(by=["Score", "Time Taken (s)"], ascending=[False, True])
        st.dataframe(leaderboard[["Name", "Score", "Time Taken (s)", "Timestamp"]].head(10))
    elif pwd:
        st.error("Incorrect password.")
