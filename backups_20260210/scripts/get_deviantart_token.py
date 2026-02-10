import os
import requests
import json
import webbrowser
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# LOAD ENV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "config", ".env"))

# CONFIG
CLIENT_ID = os.getenv("DA_CLIENT_ID")
CLIENT_SECRET = os.getenv("DA_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080/callback"
TOKEN_FILE = os.path.join(BASE_DIR, "config", "deviantart_tokens.json")

# SCOPES needed for uploading
SCOPES = "stash publish browse user"

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    print(f"\n✅ SUCCESS! Tokens saved to {TOKEN_FILE}")

def exchange_code_for_token(code):
    print(f"🔄 Exchanging code: {code}...")
    url = "https://www.deviantart.com/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)
    else:
        print(f"❌ Error getting token: {response.text}")

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: DA_CLIENT_ID or DA_CLIENT_SECRET not found in config/.env")
        return

    # 1. Authorize URL
    auth_url = f"https://www.deviantart.com/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}"
    
    print("\n=== DEVIANTART AUTHENTICATION (MANUAL MODE) ===")
    print("1. Ensure your App in https://www.deviantart.com/developers/apps has Redirect URI set to:")
    print(f"   {REDIRECT_URI}")
    print("\n2. I will open the browser. Click 'AUTHORIZE'.")
    print("3. **IMPORTANT**: After authorizing, you will be redirected to 'localhost'.")
    print("   The page will likely fail to load (Connection Refused). **THIS IS NORMAL.**")
    print("   Look at your browser's address bar. It will look like:")
    print("   http://localhost:8080/callback?code=aksjdh12389123...")
    
    webbrowser.open(auth_url)
    
    print("\n4. COPY that entire URL from the browser and paste it below:")
    
    try:
        manual_url = input("Paste URL > ").strip()
        
        # Extract Code
        if "code=" in manual_url:
            # Handle full URL or just the code
            if "?" in manual_url:
                query = urlparse(manual_url).query
                params = parse_qs(query)
                code = params.get("code", [None])[0]
            else:
                code = manual_url # Assuming user pasted just the code
                
            if code:
                exchange_code_for_token(code)
            else:
                print("❌ Could not find 'code' in the pasted URL.")
        else:
             # Try assuming the whole input is the code
             exchange_code_for_token(manual_url)

    except KeyboardInterrupt:
        print("\nProcess canceled.")

if __name__ == "__main__":
    main()
