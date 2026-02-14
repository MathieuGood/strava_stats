import math
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import CITY_A, CITY_B, RADIUS_KM, WORK_HOUR_START, WORK_HOUR_END, TIMEZONE


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distance in km between two (lat, lon) points."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class CommuteDetector:
    def __init__(self, city_a=CITY_A, city_b=CITY_B, radius_km=RADIUS_KM,
                 work_hour_start=WORK_HOUR_START, work_hour_end=WORK_HOUR_END,
                 timezone=TIMEZONE):
        self.city_a = city_a
        self.city_b = city_b
        self.radius_km = radius_km
        self.work_hour_start = work_hour_start
        self.work_hour_end = work_hour_end
        self.tz = ZoneInfo(timezone)

    def _near_city(self, latlng, city):
        if not latlng or len(latlng) < 2:
            return False
        return _haversine_km(latlng[0], latlng[1], city["lat"], city["lon"]) <= self.radius_km

    def _parse_local_dt(self, activity):
        dt_utc = datetime.fromisoformat(activity["start_date"].replace("Z", "+00:00"))
        return dt_utc.astimezone(self.tz)

    def is_commute(self, activity):
        if activity.get("sport_type") != "Ride":
            return False
        start = activity.get("start_latlng")
        end = activity.get("end_latlng")
        if not start or not end:
            return False

        # Check location: start near one city, end near the other
        a_to_b = self._near_city(start, self.city_a) and self._near_city(end, self.city_b)
        b_to_a = self._near_city(start, self.city_b) and self._near_city(end, self.city_a)
        if not (a_to_b or b_to_a):
            return False

        # Check weekday and work hours
        local_dt = self._parse_local_dt(activity)
        if local_dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False
        if not (self.work_hour_start <= local_dt.hour < self.work_hour_end):
            return False

        return True

    def detect_departure_arrival(self, activity):
        """Returns (departure_city_name, arrival_city_name)."""
        start = activity.get("start_latlng")
        end = activity.get("end_latlng")
        if self._near_city(start, self.city_a) and self._near_city(end, self.city_b):
            return self.city_a["name"], self.city_b["name"]
        return self.city_b["name"], self.city_a["name"]

    def filter_commutes(self, activities):
        """Return only activities that are commutes (raw, unmodified)."""
        return [a for a in activities if self.is_commute(a)]

    def get_commute_activities(self, activities):
        """Filter and enrich activities with commute metadata."""
        result = []
        for a in activities:
            if not self.is_commute(a):
                continue
            dep, arr = self.detect_departure_arrival(a)
            local_dt = self._parse_local_dt(a)
            result.append({
                "date": local_dt.date(),
                "datetime": local_dt,
                "departure": dep,
                "arrival": arr,
                "distance_km": a.get("distance", 0) / 1000,
                "name": a.get("name", ""),
            })
        result.sort(key=lambda x: x["datetime"])
        return result
