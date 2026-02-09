import requests
import json
import os
from dotenv import load_dotenv

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

CLIENT_ID = os.getenv("DA_CLIENT_ID")
CLIENT_SECRET = os.getenv("DA_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
CODE = "4b66926c4ed55169174436708fe2f076b1eca081"
TOKEN_FILE = os.path.join(BASE_DIR, "config", "deviantart_tokens.json")

def exchange():
    url = "https://www.deviantart.com/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": CODE,
        "redirect_uri": REDIRECT_URI
    }
    
    print(f"Exchanging code {CODE}...")
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        tokens = response.json()
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        print("SUCCESS: Token saved.")
    else:
        print(f"FAILED: {response.text}")

if __name__ == "__main__":
    exchange()
