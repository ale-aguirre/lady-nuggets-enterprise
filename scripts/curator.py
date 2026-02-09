import os
import shutil
import base64
import json
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
RAW_DIR = os.path.join(BASE_DIR, "content", "raw")
CURATED_DIR = os.path.join(BASE_DIR, "content", "curated")
REJECTED_DIR = os.path.join(BASE_DIR, "content", "rejected")
DB_PATH = os.path.join(BASE_DIR, "database", "content.db")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# SETUP GEMINI
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

CRITERIA_PROMPT = """
Analiza esta imagen NSFW anime:

PUNTAJE (0-10):
- Anatomía (manos, ojos): __/10
- Composición: __/10
- Iluminación: __/10
- Estética gótica elegante: __/10

RECHAZAR si: >5 dedos, ojos bizcos, anatomía imposible

Responde SOLO JSON sin markdown:
{"anatomy":X,"composition":X,"lighting":X,"aesthetic":X,"total":X,"tier":"premium|standard|rejected","title":"...","tags":["tag1","tag2"]}
"""

def analyze_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            img_data = image_file.read()

        response = model.generate_content([
            {"mime_type": "image/png", "data": img_data},
            CRITERIA_PROMPT
        ])
        
        text = response.text.replace('```json','').replace('```','').strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None

def process_images():
    if not os.path.exists(DB_PATH):
        # Create DB if not exists
        conn = sqlite3.connect(DB_PATH)
        conn.execute('''CREATE TABLE IF NOT EXISTS images 
                     (id INTEGER PRIMARY KEY, filename TEXT, tier TEXT, score INTEGER, title TEXT, tags TEXT, created_at TIMESTAMP, posted_da BOOLEAN DEFAULT 0, posted_tw BOOLEAN DEFAULT 0)''')
        conn.close()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure directories exist
    os.makedirs(os.path.join(CURATED_DIR, "premium"), exist_ok=True)
    os.makedirs(os.path.join(CURATED_DIR, "standard"), exist_ok=True)
    os.makedirs(REJECTED_DIR, exist_ok=True)

    for filename in os.listdir(RAW_DIR):
        if not filename.endswith(('.png', '.jpg')):
            continue
            
        filepath = os.path.join(RAW_DIR, filename)
        print(f"Analyzing {filename} with Gemini Flash...")
        
        result = analyze_image(filepath)
        
        if not result:
            print("Skipping due to error.")
            continue
            
        # Logic based on score (User requested limits: >36 Premium, >28 Standard)
        total_score = result.get('total', 0)
        
        if total_score >= 36:
            tier = 'premium'
            dest = os.path.join(CURATED_DIR, "premium", filename)
        elif total_score >= 28:
            tier = 'standard'
            dest = os.path.join(CURATED_DIR, "standard", filename)
        else:
            tier = 'rejected'
            dest = os.path.join(REJECTED_DIR, filename)
            
        shutil.move(filepath, dest)
        
        # Update DB
        cursor.execute('''
            INSERT INTO images (filename, tier, score, title, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, tier, total_score, result.get('title'), str(result.get('tags')), datetime.now()))
        
        conn.commit()
        print(f"Moved to {tier} (Score: {total_score})")
        
        # Rate limit compliance (60 req/min is plenty, but let's be safe)
        time.sleep(2)

    conn.close()

if __name__ == "__main__":
    process_images()
