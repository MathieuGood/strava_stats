"""Load activities from JSON file at startup."""

import json
import os

_activities: list[dict] = []


def load_activities() -> bool:
    global _activities
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'activities.json'))
    with open(data_path) as f:
        _activities = json.load(f)
    print(f"Loaded {len(_activities)} activities from {data_path}")
    return True


def get_activities() -> list[dict]:
    return _activities
