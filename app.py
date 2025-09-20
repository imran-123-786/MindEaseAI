import streamlit as st
import google.generativeai as genai
import sqlite3
import speech_recognition as sr
import pyttsx3
from datetime import datetime
import os

# ----------------------------
# Configure Gemini (API key via env variable)
# ----------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "your_api_key_here"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------------
# Database Setup
# ----------------------------
conn = sqlite3.connect("mindease.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS moods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mood TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

c.execute("""CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT,
                bot_reply TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

conn.commit()

# ----------------------------
# Voice Output (Safe Function)
# ----------------------------
def speak(text):
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"TTS error: {e}")

# ----------------------------
# Gemini Chat Function
# ----------------------------
def ask_gemini(query):
    try:
        response = model.generate_content(query)
        return response.text
    except Exception as e:
        return f"⚠️ Error: {e}"

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("💙 MindEase AI Prototype")
st.write("Hello baby 😘, welcome to our Generative AI mental wellness assistant!")

# ----------------------------
# Mood Tracker
# ----------------------------
st.subheader("🌈 How are you feeling today?")
mood = st.radio("Select your mood:", ["😊 Happy", "😔 Sad", "😟 Stressed", "😌 Relaxed"])

if st.button("Log Mood"):
    c.execute("INSERT INTO moods (mood) VALUES (?)", (mood,))
    conn.commit()
    st.success(f"Your mood '{mood}' has been logged 💙")
    speak(f"Your mood {mood} has been logged")

# Show mood history chart
st.subheader("📊 Your Mood History")
c.execute("SELECT timestamp, mood FROM moods ORDER BY timestamp DESC LIMIT 10")
rows = c.fetchall()
if rows:
    st.table(rows)

# ----------------------------
# Chatbot Section
# ----------------------------
st.markdown("---")
st.subheader("💬 Talk to MindEase AI")

user_input = st.text_input("💭 Share your thoughts or ask for support:")

# Voice input button
if st.button("🎤 Speak Instead"):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        st.info("Listening... please speak")
        audio = recognizer.listen(source)
    try:
        user_input = recognizer.recognize_google(audio)
        st.success(f"🗣️ You said: {user_input}")
    except sr.UnknownValueError:
        st.warning("❌ Could not understand audio")
    except sr.RequestError:
        st.error("⚠️ Speech recognition service error")

# Process chatbot input
if st.button("Submit"):
    if user_input.strip() == "":
        st.warning("Please type or speak something first 💡")
    else:
        reply = ask_gemini(user_input)
        st.success("### 🤖 Gemini’s Response:")
        st.write(reply)

        # Save to DB
        c.execute("INSERT INTO chats (user_input, bot_reply) VALUES (?, ?)", (user_input, reply))
        conn.commit()

        # Crisis detection
        if any(word in user_input.lower() for word in ["suicidal", "end my life", "kill myself"]):
            st.error("🚨 If you are in crisis, please call your local helpline immediately (e.g., 1800-599-0019 in India).")
            speak("If you are in crisis, please reach out to your local helpline immediately. You are not alone.")

        speak(reply)

# ----------------------------
# Show Previous Chat History
# ----------------------------
st.subheader("📜 Chat History")
c.execute("SELECT timestamp, user_input, bot_reply FROM chats ORDER BY timestamp DESC LIMIT 5")
chat_rows = c.fetchall()
for row in chat_rows:
    ts, u, b = row
    st.markdown(f"🧑 You ({ts}): {u}")
    st.markdown(f"🤖 Bot: {b}")
    st.markdown("---")