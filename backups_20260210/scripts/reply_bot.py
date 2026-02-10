import os
import sqlite3
import random
import time
from dotenv import load_dotenv
import google.generativeai as genai

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
GEMINI_KEY = os.getenv("GEMINI_KEY")
DB_PATH = os.path.join(BASE_DIR, "database", "interactions.db")

# SETUP GEMINI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

PERSONA_PROMPT = """
Eres Lady Nuggets, una asistente digital de arte anime.
Responde a este comentario de un fan.
Tono: Amigable, misterioso, usa 1 emoji max.
Objetivo: Agradecer y sutilmente sugerir ver más arte sin censura en Patreon si el comentario es muy positivo.
Max longitud: 1 frase.

Comentario del fan: "{comment}"
"""

def generate_reply(comment_text):
    try:
        response = model.generate_content(PERSONA_PROMPT.format(comment=comment_text))
        return response.text.strip()
    except Exception as e:
        print(f"Gemini Error: {e}")
        return "Thank you so much! 💜"

def main():
    # Placeholder for loop logic (needs platform scraping integration)
    test_comment = "Wow, she looks painfully elegant! Love the eyes."
    print(f"Comment: {test_comment}")
    
    reply = generate_reply(test_comment)
    print(f"Reply: {reply}")
    
    # Save Log
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY, comment_text TEXT, reply_text TEXT)")
    conn.execute("INSERT INTO replies (comment_text, reply_text) VALUES (?, ?)", (test_comment, reply))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
