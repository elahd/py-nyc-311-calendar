"""Utility functions"""

from datetime import datetime, date, timedelta
from typing import Union
import re
import pytz


def today():
    """Gets today's date in New York. We don't care about the user's local time. See https://en.wikipedia.org/wiki/View_of_the_World_from_9th_Avenue for reference."""
    return datetime.now(pytz.timezone("US/Eastern")).date()


def date_mod(num_days: int, p_date: date = today()):
    """Adjusts a date object — not a datetime object — by the specified number of days. Returns a date object."""
    return (
        datetime.combine(p_date, datetime.min.time()) + timedelta(days=num_days)
    ).date()


def scrubber(exp_name: Union[str, None]):
    """Scrubs (Observed) and calendar year from event names. 'Christmas Day (Observed) 2021' becomes 'Christmas Day'"""
    if exp_name is None:
        return None

    regexp = r"( *\(Observed\) *)|( *\d{4} *)"  # Captures (Observed), YYYY, and any whitespace before, after, and in between.
    return re.sub(regexp, "", exp_name)
