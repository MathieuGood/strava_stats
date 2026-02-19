import json

from .sports import resolve_sport


class ActivityStorage:
    def __init__(self, path: str):
        self._path = path

    def save(self, activities: list[dict]):
        with open(self._path, "w") as f:
            json.dump(activities, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(activities)} activities to {self._path}")

    def load(self) -> list[dict]:
        with open(self._path) as f:
            return json.load(f)

    def get_by_sport(self, sport: str) -> list[dict]:
        sport_type = resolve_sport(sport)
        return [a for a in self.load() if a.get("sport_type") == sport_type]

    def get_sport_types(self) -> list[str]:
        return sorted({a.get("sport_type") for a in self.load()})
