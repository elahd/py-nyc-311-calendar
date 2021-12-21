import logging
from datetime import date, datetime
from enum import Enum
import aiohttp

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class CivCalAPI:
    """API representation."""

    class Status(Enum):
        """Calendar item status codes."""

        UNKNOWN = 0  # Not used
        IN_EFFECT = 1
        ON_SCHEDULE = 2
        OPEN = 3
        PARTLY_OPEN = 4
        NOT_IN_SESSION = 5
        SUSPENDED = 6
        CLOSED = 7

    class EventType(Enum):
        """Types of events reported via API"""

        UNKNOWN = 0  # Not used
        PARK = 1
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
    KNOWN_EVENT_TYPES = {
        "Alternate Side Parking": {"name": "On Street Parking", "id": EventType.PARK},
        "Collections": {"name": "Garbage and Recycling", "id": EventType.TRASH},
        "Schools": {"name": "Schools", "id": EventType.SCHOOL},
    }

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ):
        self._session = session
        self._api_key = api_key
        self._request_headers = {"Ocp-Apim-Subscription-Key": api_key}

    async def get_calendar(self, start_date: date, end_date: date):
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

            for item in day["items"]:
                try:
                    event_type_id = self.KNOWN_EVENT_TYPES[item["type"]]["id"]
                    status_id = self.KNOWN_STATUSES[item["status"]]["id"]
                    description = item["details"]
                except Exception as error:
                    raise UnexpectedEntry from error

                resp_dict[cur_date] = {
                    event_type_id: {"status_id": status_id, "explanation": description}
                }

        return resp_dict

    async def __call_api(self, base_url: str, url_params: dict):
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
            return json


class UnexpectedEntry(Exception):
    pass
