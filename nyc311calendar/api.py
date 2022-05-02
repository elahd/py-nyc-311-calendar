"""NYC 311 Calendar API."""

from datetime import date, datetime, timedelta
from enum import Enum
import json
import logging
from typing import Iterable

import aiohttp

from .util import date_mod, scrubber, today

_LOGGER = logging.getLogger(__name__)


class NYC311API:
    """API representation."""

    class CalendarTypes(Enum):
        """Calendar views."""

        BY_DATE = 1
        DAYS_AHEAD = 2
        NEXT_EXCEPTIONS = 3

    class Status(Enum):
        """Calendar item status codes."""

        IN_EFFECT = 1
        ON_SCHEDULE = 2
        OPEN = 3
        PARTLY_OPEN = 4
        NOT_IN_SESSION = 5
        SUSPENDED = 6
        CLOSED = 7
        DELAYED = 8
        STAFF_ONLY = 9

    class ServiceType(Enum):
        """Types of events reported via API."""

        PARKING = 1
        SCHOOL = 2
        TRASH = 3

    CALENDAR_BASE_URL = "https://api.nyc.gov/public/api/GetCalendar"
    API_REQ_DATE_FORMAT = "%m/%d/%Y"
    API_RSP_DATE_FORMAT = "%Y%m%d"
    KNOWN_STATUSES = {
        "IN EFFECT": {
            "name": "In Effect",
            "is_exception": False,
            "routine_closure": False,
            "id": Status.IN_EFFECT,
        },
        "ON SCHEDULE": {
            "name": "On Schedule",
            "is_exception": False,
            "routine_closure": False,
            "id": Status.ON_SCHEDULE,
        },
        "OPEN": {
            "name": "Open",
            "routine_closure": False,
            "is_exception": False,
            "id": Status.OPEN,
        },
        "PARTLY OPEN": {
            "name": "Partly Open",
            "is_exception": True,
            "routine_closure": False,
            "id": Status.PARTLY_OPEN,
        },
        "NOT IN SESSION": {
            "name": "Not In Session",
            "is_exception": False,
            "routine_closure": True,
            "id": Status.NOT_IN_SESSION,
        },
        "NOT IN EFFECT": {
            "name": "Not In Effect",
            "is_exception": False,
            "routine_closure": True,
            "id": Status.NOT_IN_SESSION,
        },
        "SUSPENDED": {
            "name": "Suspended",
            "is_exception": True,
            "routine_closure": False,
            "id": Status.SUSPENDED,
        },
        "CLOSED": {
            "name": "Closed",
            "routine_closure": False,
            "is_exception": True,
            "id": Status.CLOSED,
        },
        "DELAYED": {
            "name": "Delayed",
            "routine_closure": False,
            "is_exception": True,
            "id": Status.DELAYED,
        },
        "STAFF ONLY": {
            "name": "Staff Only",
            "routine_closure": False,
            "is_exception": True,
            "id": Status.STAFF_ONLY,
        },
    }
    KNOWN_SERVICES = {
        "Alternate Side Parking": {
            "name": "Parking",
            "id": ServiceType.PARKING,
            "exception_name": "Rule Suspension",
        },
        "Collections": {
            "name": "Sanitation",
            "id": ServiceType.TRASH,
            "exception_name": "Collection Suspension",
        },
        "Schools": {
            "name": "School",
            "id": ServiceType.SCHOOL,
            "exception_name": "Closure",
        },
    }

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ):
        """Create new API controller with existing aiohttp session."""
        self._session = session
        self._api_key = api_key
        self._request_headers = {"Ocp-Apim-Subscription-Key": api_key}

        self.status_by_id = {}
        for _, value in self.KNOWN_STATUSES.items():
            self.status_by_id[value["id"]] = {
                "name": value["name"],
                "is_exception": value["is_exception"],
                "routine_closure": value["routine_closure"],
            }

        self.service_by_id = {}
        for _, value in self.KNOWN_SERVICES.items():
            self.service_by_id[value["id"]] = {
                "name": value["name"],
                "exception_name": value["exception_name"],
            }

    async def get_calendar(
        self,
        calendars: list[CalendarTypes] = [
            CalendarTypes.BY_DATE,
            CalendarTypes.DAYS_AHEAD,
            CalendarTypes.NEXT_EXCEPTIONS,
        ],
        scrub: bool = False,
    ) -> dict:
        """Retrieve calendar data."""
        resp_dict = {}

        start_date = date_mod(-1)
        end_date = date_mod(90, start_date)
        api_resp = await self.__async_calendar_update(start_date, end_date, scrub)

        for calendar in calendars:
            if calendar is self.CalendarTypes.BY_DATE:
                resp_dict[self.CalendarTypes.BY_DATE] = api_resp
            elif calendar is self.CalendarTypes.DAYS_AHEAD:
                resp_dict[
                    self.CalendarTypes.DAYS_AHEAD
                ] = await self.__build_days_ahead(api_resp)
            elif calendar is self.CalendarTypes.NEXT_EXCEPTIONS:
                resp_dict[
                    self.CalendarTypes.NEXT_EXCEPTIONS
                ] = await self.__build_next_exceptions(api_resp)

        _LOGGER.debug("Got calendar.")

        return resp_dict

    async def __async_calendar_update(
        self, start_date: date, end_date: date, scrub: bool = False
    ) -> dict:
        """Get events for specified date range."""

        date_params = {
            "fromdate": start_date.strftime(self.API_REQ_DATE_FORMAT),
            "todate": end_date.strftime(self.API_REQ_DATE_FORMAT),
        }
        base_url = self.CALENDAR_BASE_URL

        resp_json = await self.__call_api(base_url, date_params)

        resp_dict = {}
        for day in resp_json["days"]:
            cur_date = datetime.strptime(
                day["today_id"], self.API_RSP_DATE_FORMAT
            ).date()

            day_dict = {}
            for item in day["items"]:
                try:
                    service_id = self.KNOWN_SERVICES[item["type"]]["id"]
                    status_id = self.KNOWN_STATUSES[item["status"]]["id"]
                    description = item.get("details")
                    exception_reason = (lambda x: scrubber(x) if scrub else x)(
                        item.get("exceptionName")
                    )
                except KeyError as error:
                    _LOGGER.error(
                        """\n\nEncountered unknown service or status. Please report this to the developers using the "Unknown Service or Status" bug template at https://github.com/elahd/nyc311calendar/issues/new/choose.\n\n"""
                        """===BEGIN COPYING HERE===\n"""
                        """Item ID: %s\n"""
                        """Day: %s\n"""
                        """===END COPYING HERE===\n""",
                        item.get("exceptionName", ""),
                        day,
                    )
                    raise self.UnexpectedEntry from error

                day_dict[service_id] = {
                    "service_name": self.service_by_id[service_id]["name"],
                    "status_id": status_id,
                    "status_name": self.status_by_id[status_id]["name"],
                    "description": description,
                    "exception_reason": ""
                    if exception_reason is None
                    else exception_reason,
                    "exception_name": self.service_by_id[service_id]["exception_name"],
                    "is_exception": self.status_by_id[status_id]["is_exception"],
                    "routine_closure": self.status_by_id[status_id]["routine_closure"],
                }

            resp_dict[cur_date] = day_dict

        _LOGGER.debug("Updated calendar.")

        return resp_dict

    async def __build_days_ahead(self, resp_dict: dict) -> dict:
        """Build dict of statuses keyed by number of days from today."""
        days_ahead = {}
        for i in list(range(-1, 7)):
            i_date = date_mod(i)
            day: dict = {"date": i_date}
            tmp_services: dict = {}
            for _, value in self.KNOWN_SERVICES.items():
                tmp_services[value["id"]] = resp_dict[i_date][value["id"]]
            day["services"] = tmp_services
            days_ahead[i] = day

        _LOGGER.debug("Built days ahead.")

        return days_ahead

    async def __build_next_exceptions(self, resp_dict: dict) -> dict:
        """Build dict of next exception for all known types."""
        next_exceptions: dict = {}
        previous_date = None
        for key, value in resp_dict.items():

            # We don't want to show yesterday's calendar event as a next exception. Skip over if date is yesterday.
            if key == (today() - timedelta(days=1)):
                continue

            # Assuming that array is already sorted by date. This is dangerous, but we're being
            # lazy. Previous_date will help verify order. We'll die abruptly if order is incorrect.
            if previous_date is None:
                previous_date = key

            if key < previous_date:
                raise self.DateOrderException("resp_dict not sorted by date.")

            for svc, svc_details in value.items():
                if (
                    next_exceptions.get(svc)
                    or not self.status_by_id[svc_details["status_id"]]["is_exception"]
                ):
                    continue

                next_exceptions[svc] = {**svc_details, "date": key}

        _LOGGER.debug("Built next exceptions.")

        return next_exceptions

    async def __call_api(self, base_url: str, url_params: dict) -> dict:
        try:
            async with self._session.get(
                base_url,
                params=url_params,
                headers=self._request_headers,
                raise_for_status=True,
                timeout=60,
                ssl=True,
            ) as resp:
                resp_json = await resp.json()
                _LOGGER.debug("got %s", resp_json)

        except aiohttp.ClientResponseError as error:
            if error.status in range(400, 500):
                raise self.InvalidAuth from error
            else:
                raise self.CannotConnect from error
        except Exception as error:
            raise self.CannotConnect from error

        _LOGGER.debug("Called API.")

        return dict(resp_json)

    class UnexpectedEntry(Exception):
        """Thrown when API returns unexpected "key"."""

    class DateOrderException(Exception):
        """Thrown when iterable that is expected to be sorted by date is not."""

    class CannotConnect(Exception):
        """Thrown when server is unreachable."""

    class InvalidAuth(Exception):
        """Thrown when login fails."""
