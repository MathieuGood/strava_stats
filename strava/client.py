from datetime import datetime

import requests

from .auth import StravaAuth


class StravaClient:
    BASE_URL = "https://www.strava.com/api/v3"

    def __init__(self, auth: StravaAuth):
        self._auth = auth
        self._session = requests.Session()

    @property
    def _headers(self):
        return {"Authorization": f"Bearer {self._auth.access_token}"}

    def fetch_all_activities(
        self,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[dict]:
        params = {"per_page": 200}
        if after:
            params["after"] = int(after.timestamp())
        if before:
            params["before"] = int(before.timestamp())

        activities = []
        page = 1

        while True:
            print(f"Fetching page {page}...")
            params["page"] = page
            resp = self._session.get(
                f"{self.BASE_URL}/athlete/activities",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            batch = resp.json()

            if not batch:
                break

            activities.extend(batch)
            print(f"  Got {len(batch)} activities (total: {len(activities)})")
            page += 1

        return activities
