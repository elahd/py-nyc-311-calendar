"""Retrieves next exception for each service category."""

from __future__ import annotations

import asyncio

import aiohttp

from nyc311calendar import NYC311API, CalendarType

API_KEY = "YOUR_API_KEY"


async def main() -> None:
    """Retrieve and print calendar."""
    async with aiohttp.ClientSession() as session:
        calendar = NYC311API(session, API_KEY)
        resp = await calendar.get_calendar(calendars=[CalendarType.NEXT_EXCEPTIONS])

        print(resp)

    await session.close()


asyncio.run(main())
