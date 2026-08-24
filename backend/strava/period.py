"""Reporting period helpers.

A reporting period runs from the 21st of the previous month to the 20th of
the month it is named after:

    "January 2026" -> Dec 21 2025 .. Jan 20 2026

Both the CLI (`main.py --report`) and the web endpoint use these helpers so
that a given month always produces the same rows.
"""

from datetime import date


def period_bounds(year: int, month: int) -> tuple[date, date]:
    """Return the (start, end) dates, inclusive, of a reporting period."""
    prev_month = 12 if month == 1 else month - 1
    prev_year = year - 1 if month == 1 else year
    return date(prev_year, prev_month, 21), date(year, month, 20)


def period_of_date(d: date) -> tuple[int, int]:
    """Return the (year, month) reporting period a date belongs to.

    E.g. Dec 22 -> (year + 1, 1) = January of next year.
         Jan 5  -> (year, 1)     = January.
         Jan 21 -> (year, 2)     = February.
    """
    if d.day >= 21:
        if d.month == 12:
            return d.year + 1, 1
        return d.year, d.month + 1
    return d.year, d.month


def iter_periods(start: tuple[int, int], end: tuple[int, int]):
    """Yield every (year, month) period from start to end, inclusive."""
    year, month = start
    while (year, month) <= end:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
