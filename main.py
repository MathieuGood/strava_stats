import os
import sys

from strava import StravaAuth, StravaClient, ActivityStorage, ActivityStats

DATA_DIR = os.path.dirname(__file__)


def main():
    storage = ActivityStorage(os.path.join(DATA_DIR, "activities.json"))

    if "--fetch" in sys.argv:
        auth = StravaAuth()
        client = StravaClient(auth)
        activities = client.fetch_all_activities()
        print(f"\nFetched {len(activities)} activities total.")
        storage.save(activities)

    # Stats on all activities
    stats = ActivityStats(storage.load())

    print(f"\n--- Total km by sport ---")
    for sport, km in stats.total_km_by_sport().items():
        print(f"  {sport}: {km:.1f} km")

    print(f"\n--- Total km by year and sport ---")
    for year, sports in stats.total_km_by_year_and_sport().items():
        print(f"\n  {year}:")
        for sport, km in sports.items():
            print(f"    {sport}: {km:.1f} km")

    # Filtered examples
    print(f"\n--- Inline skating in 2025 ---")
    inline_2025 = stats.by_sport("inline skating").by_year(2025)
    print(f"  {inline_2025.total_km():.1f} km")
    print(f"\n--- Biking in 2025 ---")
    biking_2025 = stats.by_sport("biking").by_year(2025)
    print(f"  {biking_2025.total_km():.1f} km")


if __name__ == "__main__":
    main()
