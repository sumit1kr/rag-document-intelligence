import os
import google.generativeai as genai
from dotenv import load_dotenv

# Configure from environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise EnvironmentError("Missing GEMINI_API_KEY in environment")

genai.configure(api_key=API_KEY)

# Create the model (Gemini Pro is used here)
model = genai.GenerativeModel('gemini-pro')

# Start a chat session (optional but useful for multi-turn memory)
chat = model.start_chat()

print("💬 Ask anything (type 'exit' to quit)\n")

# Main input loop
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Exiting chat.")
        break
    try:
        response = chat.send_message(user_input)
        print("AI:", response.text.strip())
    except Exception as e:
        print("⚠️ Error:", e)
