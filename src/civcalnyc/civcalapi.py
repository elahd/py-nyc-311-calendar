"""CivCalNYC API"""

import logging
from datetime import date, datetime
from enum import Enum
import aiohttp
from .util import date_mod, scrubber

_LOGGER = logging.getLogger(__name__)


class CivCalAPI:
    """API representation."""

    class CalendarTypes(Enum):
        """Calendar types to be returned by CivCalAPI"""

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

    class ServiceType(Enum):
        """Types of events reported via API"""

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
            "id": Status.IN_EFFECT,
        },
        "ON SCHEDULE": {
            "name": "On Schedule",
            "is_exception": False,
            "id": Status.ON_SCHEDULE,
        },
        "OPEN": {"name": "Open", "is_exception": False, "id": Status.OPEN},
        "PARTLY OPEN": {
            "name": "Partly Open",
            "is_exception": True,
            "id": Status.PARTLY_OPEN,
        },
        "NOT IN SESSION": {
            "name": "Not In Session",
            "is_exception": False,
            "id": Status.NOT_IN_SESSION,
        },
        "NOT IN EFFECT": {
            "name": "Not In Effect",
            "is_exception": False,
            "id": Status.NOT_IN_SESSION,
        },
        "SUSPENDED": {
            "name": "Suspended",
            "is_exception": True,
            "id": Status.SUSPENDED,
        },
        "CLOSED": {"name": "Closed", "is_exception": True, "id": Status.CLOSED},
    }
    KNOWN_SERVICES = {
        "Alternate Side Parking": {
            "name": "Alternate Side Parking",
            "id": ServiceType.PARKING,
            "exception_name": "Rule Suspension",
        },
        "Collections": {
            "name": "Garbage and Recycling",
            "id": ServiceType.TRASH,
            "exception_name": "Collection Change",
        },
        "Schools": {
            "name": "Schools",
            "id": ServiceType.SCHOOL,
            "exception_name": "Closure",
        },
    }

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ):
        self._session = session
        self._api_key = api_key
        self._request_headers = {"Ocp-Apim-Subscription-Key": api_key}

        self.status_by_id = {}
        for _, value in self.KNOWN_STATUSES.items():
            self.status_by_id[value["id"]] = {
                "name": value["name"],
                "is_exception": value["is_exception"],
            }

        self.service_by_id = {}
        for _, value in self.KNOWN_SERVICES.items():
            self.service_by_id[value["id"]] = {
                "name": value["name"],
                "exception_name": value["exception_name"],
            }

    async def get_calendar(
        self,
        calendars=(
            CalendarTypes.BY_DATE,
            CalendarTypes.DAYS_AHEAD,
            CalendarTypes.NEXT_EXCEPTIONS,
        ),
        scrub: bool = False,
    ):
        """Main function to retrieve calendars from this library."""
        resp_dict = {}

        start_date = date_mod(-1)
        end_date = date_mod(90, start_date)
        api_resp = await self.__async_calendar_update(start_date, end_date, scrub)

        for calendar in calendars:
            if calendar is self.CalendarTypes.BY_DATE:
                resp_dict[calendar] = api_resp
            elif calendar is self.CalendarTypes.DAYS_AHEAD:
                resp_dict[calendar] = await self.__build_days_ahead(api_resp)
            elif calendar is self.CalendarTypes.NEXT_EXCEPTIONS:
                resp_dict[calendar] = await self.__build_next_exceptions(api_resp)

        _LOGGER.debug("Got calendar.")

        return resp_dict

    async def __async_calendar_update(
        self, start_date: date, end_date: date, scrub: bool = False
    ):
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
                    description = item["details"]
                    exception_name = (lambda x: scrubber(x) if scrub else x)(
                        item.get("exceptionName")
                    )
                except Exception as error:
                    raise self.UnexpectedEntry from error

                day_dict[service_id] = {
                    "service_name": self.service_by_id[service_id]["name"],
                    "status_id": status_id,
                    "status_name": self.status_by_id[status_id]["name"],
                    "description": description,
                    "exception_name": exception_name,
                }

            resp_dict[cur_date] = day_dict

        _LOGGER.debug("Updated calendar.")

        return resp_dict

    async def __build_days_ahead(self, resp_dict):
        """Builds dict of statuses keyed by number of days from today."""
        days_ahead = {}
        for i in list(range(-1, 7)):
            i_date = date_mod(i)
            day = {"date": i_date}
            for _, value in self.KNOWN_SERVICES.items():
                day[value["id"]] = resp_dict[i_date][value["id"]]
            days_ahead[i] = day

        _LOGGER.debug("Built days ahead.")

        return days_ahead

    async def __build_next_exceptions(self, resp_dict):
        """Builds dict of next exception for all known types."""
        next_exceptions = {}
        previous_date = None
        for key, value in resp_dict.items():
            # Assuming that array is already sorted by date. This is dangerous, but we're being
            # lazy. Previous_date will help verify order. We'll die abruptly if order is incorrect.

            if previous_date is None:
                previous_date = key
            elif key < previous_date:
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

    async def __call_api(self, base_url: str, url_params: dict):
        try:
            async with self._session.get(
                base_url,
                params=url_params,
                headers=self._request_headers,
                raise_for_status=True,
                timeout=60,
                ssl=True,
            ) as resp:
                json = await resp.json()
                _LOGGER.debug("got %s", json)

        except aiohttp.ClientResponseError as error:
            if error.status in range(400, 500):
                raise self.InvalidAuth from error
            else:
                raise self.CannotConnect from error
        except Exception as error:
            raise self.CannotConnect from error

        _LOGGER.debug("Called API.")

        return json

    class UnexpectedEntry(Exception):
        """Thrown when API returns unexpected "key"."""

    class DateOrderException(Exception):
        """Thrown when iterable that is expected to be sorted by date is not."""

    class CannotConnect(Exception):
        """Thrown when server is unreachable."""

    class InvalidAuth(Exception):
        """Thrown when login fails."""
