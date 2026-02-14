import os
import sys

from strava import StravaAuth, StravaClient, ActivityStorage, ActivityStats
from strava import CommuteDetector, CommuteReport

DATA_DIR = os.path.dirname(__file__)


def main():
    storage = ActivityStorage(os.path.join(DATA_DIR, "activities.json"))

    if "--fetch" in sys.argv:
        auth = StravaAuth()
        client = StravaClient(auth)
        activities = client.fetch_all_activities()
        print(f"\nFetched {len(activities)} activities total.")
        storage.save(activities)

    # Check for --report flag
    if "--report" in sys.argv:
        idx = sys.argv.index("--report")
        if idx + 1 >= len(sys.argv):
            print("Usage: --report YYYY-MM")
            sys.exit(1)
        year_month = sys.argv[idx + 1]
        try:
            year, month = year_month.split("-")
            year, month = int(year), int(month)
        except ValueError:
            print("Invalid format. Use --report YYYY-MM")
            sys.exit(1)

        activities = storage.load()
        detector = CommuteDetector()
        commutes = detector.get_commute_activities(activities)
        # Filter to requested month
        commutes = [
            c for c in commutes if c["date"].year == year and c["date"].month == month
        ]

        if not commutes:
            print(f"No commute activities found for {year}-{month:02d}")
            sys.exit(0)

        report = CommuteReport(commutes, year, month)
        filepath = report.generate(output_dir=os.path.join(DATA_DIR, "reports"))
        print(
            f"Generated report with {len(commutes)} trips over {len(set(c['date'] for c in commutes))} days"
        )
        print(f"Total distance: {sum(c['distance_km'] for c in commutes):.1f} km")
        print(f"Saved to: {filepath}")
        return

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

    print(f"\n--- Commute activities in 2025 ---")
    detector = CommuteDetector()
    commute_activities = detector.filter_commutes(storage.load())
    commute_stats = ActivityStats(commute_activities).by_year(2025)
    for sport, km in commute_stats.total_km_by_sport().items():
        print(f"  {sport}: {km:.1f} km")


if __name__ == "__main__":
    main()
