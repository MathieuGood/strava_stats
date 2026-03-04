"""
One-shot Strava re-authorization script.
Run this when your access/refresh tokens are invalid and need a full OAuth reset.

Steps:
  1. Run this script — it prints an authorization URL
  2. Open the URL in your browser, authorize the app
  3. You'll be redirected to http://localhost/... (won't load — that's fine)
  4. Copy the `code=` value from the URL bar and paste it here
  5. New tokens are saved to .env automatically
"""
import os
import webbrowser
import requests
from dotenv import load_dotenv

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH, override=True)

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

auth_url = (
    f"https://www.strava.com/oauth/authorize"
    f"?client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri=http://localhost"
    f"&approval_prompt=force"
    f"&scope=activity:read_all"
)

print("Opening Strava authorization page...")
print(f"\n  {auth_url}\n")
webbrowser.open(auth_url)

code = input("Paste the 'code' value from the redirect URL: ").strip()

resp = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    },
)
resp.raise_for_status()
data = resp.json()

access_token = data["access_token"]
refresh_token = data["refresh_token"]
expires_at = data["expires_at"]

with open(ENV_PATH, "w") as f:
    f.write(f"CLIENT_ID={CLIENT_ID}\n")
    f.write(f"CLIENT_SECRET={CLIENT_SECRET}\n")
    f.write(f"ACCESS_TOKEN={access_token}\n")
    f.write(f"REFRESH_TOKEN={refresh_token}\n")
    f.write(f"EXPIRES_AT={expires_at}\n")

print(f"\nTokens saved to .env (expires_at={expires_at})")
print("You can now run: uv run main.py --fetch")
