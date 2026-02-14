import os
import time

import requests
from dotenv import load_dotenv


class StravaAuth:
    TOKEN_URL = "https://www.strava.com/oauth/token"

    def __init__(self, env_path=None):
        self._env_path = env_path or os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(self._env_path)

        self._client_id = os.environ["CLIENT_ID"]
        self._client_secret = os.environ["CLIENT_SECRET"]
        self._access_token = os.environ["ACCESS_TOKEN"]
        self._refresh_token = os.environ["REFRESH_TOKEN"]
        self._expires_at = int(os.environ["EXPIRES_AT"])

    @property
    def access_token(self):
        if time.time() >= self._expires_at - 60:
            self._refresh()
        return self._access_token

    def _refresh(self):
        print("Access token expired, refreshing...")
        resp = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._expires_at = data["expires_at"]
        self._persist()
        print("Token refreshed successfully.")

    def _persist(self):
        with open(self._env_path, "w") as f:
            f.write(f"CLIENT_ID={self._client_id}\n")
            f.write(f"CLIENT_SECRET={self._client_secret}\n")
            f.write(f"ACCESS_TOKEN={self._access_token}\n")
            f.write(f"REFRESH_TOKEN={self._refresh_token}\n")
            f.write(f"EXPIRES_AT={self._expires_at}\n")
