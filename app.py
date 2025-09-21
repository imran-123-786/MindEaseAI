import streamlit as st
import google.generativeai as genai
import sqlite3

import os

# ----------------------------
# Load API Key Safely
# ----------------------------
# Use Streamlit secrets instead of dotenv for cloud deployment
if 'GOOGLE_API_KEY' in st.secrets:
    api_key = st.secrets['GOOGLE_API_KEY']
else:
    # Fallback for local development
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("❌ API key not found! Please set GOOGLE_API_KEY in Streamlit secrets or environment variables.")
else:
    genai.configure(api_key=api_key)
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
st.write("Hello! Welcome to our Generative AI mental wellness assistant!")

# ----------------------------
# Mood Tracker
# ----------------------------
st.subheader("🌈 How are you feeling today?")
mood = st.radio("Select your mood:", ["😊 Happy", "😔 Sad", "😟 Stressed", "😌 Relaxed"])

if st.button("Log Mood"):
    c.execute("INSERT INTO moods (mood) VALUES (?)", (mood,))
    conn.commit()
    st.success(f"Your mood '{mood}' has been logged 💙")

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

# Process chatbot input
if st.button("Submit"):
    if user_input.strip() == "":
        st.warning("Please type something first 💡")
    else:
        with st.spinner("Thinking..."):
            reply = ask_gemini(user_input)
        
        st.success("### 🤖 Gemini's Response:")
        st.write(reply)

        # Save to DB
        c.execute("INSERT INTO chats (user_input, bot_reply) VALUES (?, ?)", (user_input, reply))
        conn.commit()

        # Crisis detection
        crisis_keywords = ["suicidal", "end my life", "kill myself", "want to die", "harm myself"]
        if any(word in user_input.lower() for word in crisis_keywords):
            st.error("🚨 If you are in crisis, please call your local helpline immediately (e.g., 1800-599-0019 in India).")
            st.info("You can also text HOME to 741741 to connect with a crisis counselor in many countries.")

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

# ----------------------------
# Resources Section
# ----------------------------
st.markdown("---")
st.subheader("📚 Mental Health Resources")
st.write("""
- National Suicide Prevention Lifeline: 1-800-273-8255 (US)
- Crisis Text Line: Text HOME to 741741 (US)
- International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/
- Mental Health America: https://www.mhanational.org/
""")

# Close database connection when done
conn.close()
