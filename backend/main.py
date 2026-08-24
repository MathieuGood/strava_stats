import os
import sys

from strava import StravaAuth, StravaClient, ActivityStorage, ActivityStats
from strava import CommuteDetector, CommuteReport
from strava import iter_periods, period_bounds

DATA_DIR = os.path.dirname(__file__)


def parse_period(text: str) -> tuple[int, int]:
    """Parse "YYYY-MM" into a (year, month) reporting period."""
    try:
        year, month = text.split("-")
        year, month = int(year), int(month)
    except ValueError:
        raise ValueError(f"Invalid period {text!r}. Use YYYY-MM")
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month in {text!r}. Use YYYY-MM")
    return year, month


def parse_periods(args: list[str]) -> list[tuple[int, int]]:
    """Expand CLI arguments into reporting periods.

    Accepts single periods ("2026-04"), ranges ("2026-04..2026-07"), or any
    mix of both. The result is de-duplicated and sorted.
    """
    periods: list[tuple[int, int]] = []
    for arg in args:
        if ".." in arg:
            first, _, last = arg.partition("..")
            start, end = parse_period(first), parse_period(last)
            if end < start:
                raise ValueError(f"Invalid range {arg!r}: end is before start")
            periods.extend(iter_periods(start, end))
        else:
            periods.append(parse_period(arg))
    return sorted(set(periods))


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
        args = []
        for arg in sys.argv[idx + 1 :]:
            if arg.startswith("--"):
                break
            args.append(arg)
        if not args:
            print("Usage: --report YYYY-MM [YYYY-MM ...] | --report YYYY-MM..YYYY-MM")
            sys.exit(1)

        try:
            periods = parse_periods(args)
        except ValueError as e:
            print(e)
            sys.exit(1)

        activities = storage.load()
        detector = CommuteDetector()
        all_commutes = detector.get_commute_activities(activities)

        for year, month in periods:
            start_date, end_date = period_bounds(year, month)
            commutes = [c for c in all_commutes if start_date <= c["date"] <= end_date]

            if not commutes:
                print(
                    f"{year}-{month:02d}: no commute activities between "
                    f"{start_date:%d/%m/%Y} and {end_date:%d/%m/%Y} - skipped"
                )
                continue

            report = CommuteReport(commutes, year, month)
            filepath = report.generate(output_dir=os.path.join(DATA_DIR, "reports"))
            days = len(set(c["date"] for c in commutes))
            total_km = sum(c["distance_km"] for c in commutes)
            print(
                f"{year}-{month:02d} ({start_date:%d/%m} -> {end_date:%d/%m}): "
                f"{len(commutes)} trips over {days} days, {total_km:.1f} km "
                f"-> {filepath}"
            )
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
