from collections import defaultdict
from datetime import datetime

from .filter import ActivityFilter
from .sports import resolve_sport


class ActivityStats:
    def __init__(self, activities: list[dict]):
        self._filter = ActivityFilter(activities)

    def total_km(self) -> float:
        return sum(a.get("distance", 0) for a in self._filter.activities) / 1000

    def total_km_by_sport(self) -> dict[str, float]:
        totals = defaultdict(float)
        for a in self._filter.activities:
            totals[a.get("sport_type", "Unknown")] += a.get("distance", 0)
        return {sport: dist / 1000 for sport, dist in sorted(totals.items())}

    def total_km_by_year(self) -> dict[int, float]:
        totals = defaultdict(float)
        for a in self._filter.activities:
            year = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00")).year
            totals[year] += a.get("distance", 0)
        return {year: dist / 1000 for year, dist in sorted(totals.items())}

    def total_km_by_year_and_sport(self) -> dict[int, dict[str, float]]:
        totals = defaultdict(lambda: defaultdict(float))
        for a in self._filter.activities:
            year = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00")).year
            sport = a.get("sport_type", "Unknown")
            totals[year][sport] += a.get("distance", 0)
        return {
            year: {sport: dist / 1000 for sport, dist in sorted(sports.items())}
            for year, sports in sorted(totals.items())
        }

    def by_sport(self, sport: str) -> "ActivityStats":
        return ActivityStats(self._filter.by_sport(sport).activities)

    def by_year(self, year: int) -> "ActivityStats":
        return ActivityStats(self._filter.by_year(year).activities)

    def by_date_range(self, after: datetime, before: datetime) -> "ActivityStats":
        return ActivityStats(self._filter.by_date_range(after, before).activities)
