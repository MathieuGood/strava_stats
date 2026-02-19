from datetime import datetime

from .sports import resolve_sport


class ActivityFilter:
    def __init__(self, activities: list[dict]):
        self._activities = activities

    def by_sport(self, sport: str) -> "ActivityFilter":
        sport_type = resolve_sport(sport)
        return ActivityFilter([a for a in self._activities if a.get("sport_type") == sport_type])

    def by_year(self, year: int) -> "ActivityFilter":
        return self.by_date_range(datetime(year, 1, 1), datetime(year + 1, 1, 1))

    def by_date_range(self, after: datetime, before: datetime) -> "ActivityFilter":
        filtered = []
        for a in self._activities:
            dt = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))
            naive = dt.replace(tzinfo=None)
            if after <= naive < before:
                filtered.append(a)
        return ActivityFilter(filtered)

    def sport_types(self) -> list[str]:
        return sorted({a.get("sport_type") for a in self._activities})

    @property
    def activities(self) -> list[dict]:
        return self._activities

    def __len__(self) -> int:
        return len(self._activities)
