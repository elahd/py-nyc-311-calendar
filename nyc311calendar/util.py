"""Utility functions."""

from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
import re

from zoneinfo import ZoneInfo


def today() -> date:
    """Get today's date in New York. We don't care about the user's local time. See https://en.wikipedia.org/wiki/View_of_the_World_from_9th_Avenue for reference."""
    return datetime.now(ZoneInfo("America/New_York")).date()


def date_mod(num_days: int, p_date: date = today()) -> date:
    """Adjust a date object — not a datetime object — by the specified number of days. Returns a date object."""
    return (
        datetime.combine(p_date, datetime.min.time()) + timedelta(days=num_days)
    ).date()


def remove_observed(exp_name: str | None) -> str | None:
    """Scrub (Observed) and calendar year from event names. 'Christmas Day (Observed) 2021' becomes 'Christmas Day'."""
    if exp_name is None:
        return None

    regexp = (  # Captures (Observed), YYYY, and any whitespace before, after, and in between.
        r"( *\(Observed\) *)|( *\d{4} *)"
    )
    return re.sub(regexp, "", exp_name)
