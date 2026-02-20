"""Load activities from JSON file at startup."""

import json
import os

DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'activities.json'))

_activities: list[dict] = []


def load_activities() -> bool:
    global _activities
    with open(DATA_PATH) as f:
        _activities = json.load(f)
    print(f"Loaded {len(_activities)} activities from {DATA_PATH}")
    return True


def get_activities() -> list[dict]:
    return _activities
