"""NYC 311 Calendar API."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import timedelta
from enum import Enum
import logging

import aiohttp
from nyc311calendar.services import Parking
from nyc311calendar.services import Sanitation
from nyc311calendar.services import School
from nyc311calendar.services import Service
from nyc311calendar.services import ServiceType
from nyc311calendar.services import ServiceTypeProfile
from nyc311calendar.services import StatusTypeProfile

from .util import date_mod
from .util import remove_observed
from .util import today

__version__ = "v0.3"


log = logging.getLogger(__name__)


class CalendarType(Enum):
    """Calendar views."""

    BY_DATE = 1
    DAYS_AHEAD = 2
    NEXT_EXCEPTIONS = 3


@dataclass
class CalendarDayEntry:
    """Entry for each service within a day."""

    service_profile: ServiceTypeProfile
    status_profile: StatusTypeProfile | None
    exception_reason: str
    raw_description: str
    date: date


class NYC311API:
    """API representation."""

    CALENDAR_BASE_URL = "https://api.nyc.gov/public/api/GetCalendar"
    API_REQ_DATE_FORMAT = "%m/%d/%Y"
    API_RSP_DATE_FORMAT = "%Y%m%d"

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
    ):
        """Create new API controller with existing aiohttp session."""
        self._session = session
        self._api_key = api_key
        self._request_headers = {"Ocp-Apim-Subscription-Key": api_key}

    async def get_calendar(
        self,
        calendars: list[CalendarType] | None = None,
        scrub: bool = True,
    ) -> dict:
        """Primary function for getting calendars from API.

        Args:
            calendars (list[CalendarType] | None, optional): List of CalendarTypes to be retrieved. Defaults to None.
            scrub (bool, optional): Whether to scrub "(Observed)" from names of holidays. (Observed) is used to indicate that, say, schools are closed on a Friday for the official observation of a holidays that falls on a weekend. Defaults to True.

        Returns:
            dict: Dictionary of calendars.
        """

        if not calendars:
            calendars = [
                CalendarType.BY_DATE,
                CalendarType.DAYS_AHEAD,
                CalendarType.NEXT_EXCEPTIONS,
            ]

        resp_dict = {}

        start_date = date_mod(-1)
        end_date = date_mod(90, start_date)
        api_resp = await self.__async_calendar_update(start_date, end_date, scrub)

        for calendar in calendars:
            if calendar is CalendarType.BY_DATE:
                resp_dict[CalendarType.BY_DATE] = api_resp
            elif calendar is CalendarType.DAYS_AHEAD:
                resp_dict[CalendarType.DAYS_AHEAD] = self.__build_days_ahead(api_resp)
            elif calendar is CalendarType.NEXT_EXCEPTIONS:
                resp_dict[CalendarType.NEXT_EXCEPTIONS] = self.__build_next_exceptions(
                    api_resp
                )

        log.info("Got calendar.")

        log.debug(resp_dict)

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
                    # Get Raw
                    raw_service_name = item["type"]
                    raw_status = item["status"]
                    raw_description = item.get("details")
                    scrubbed_exception_reason = (
                        lambda x: remove_observed(x) if scrub else x
                    )(item.get("exceptionName"))

                    # Process
                    service_type = ServiceType(raw_service_name)

                    status_type: School.StatusType | Parking.StatusType | Sanitation.StatusType
                    service_class: type[School] | type[Parking] | type[Sanitation]

                    if service_type == ServiceType.SCHOOL:
                        service_class = School
                        status_type = School.StatusType(raw_status)
                        status_profile = School.STATUS_MAP[status_type]

                    elif service_type == ServiceType.PARKING:
                        service_class = Parking
                        status_type = Parking.StatusType(raw_status)
                        status_profile = Parking.STATUS_MAP[status_type]

                    elif service_type == ServiceType.SANITATION:
                        service_class = Sanitation
                        status_type = Sanitation.StatusType(raw_status)
                        status_profile = Sanitation.STATUS_MAP[status_type]

                except (KeyError, AttributeError) as error:
                    log.error(
                        """\n\nEncountered unknown service or status. Please report this to the developers using the "Unknown Service or Status" bug template at https://github.com/elahd/nyc311calendar/issues/new/choose.\n\n"""
                        """===BEGIN COPYING HERE===\n"""
                        """Item ID: %s\n"""
                        """Day: %s\n"""
                        """===END COPYING HERE===\n""",
                        item.get("exceptionName", ""),
                        day,
                    )
                    raise self.UnexpectedEntry from error

                day_dict[service_type] = CalendarDayEntry(
                    service_profile=service_class.PROFILE,
                    status_profile=status_profile
                    if isinstance(status_profile, StatusTypeProfile)
                    else None,
                    exception_reason=""
                    if scrubbed_exception_reason is None
                    else scrubbed_exception_reason,
                    raw_description=raw_description,
                    date=cur_date,
                )

            resp_dict[cur_date] = day_dict

        log.debug("Updated calendar.")

        return resp_dict

    @classmethod
    def __build_days_ahead(cls, resp_dict: dict) -> dict:
        """Build dict of statuses keyed by number of days from today."""

        # Dictionary Format
        # {
        #     "-1": {
        #         "date": "2022-05-19",
        #         "services": {
        #             ServiceType.PARKING: {
        #                 (CalendarDayEntry)
        #             },
        #             ServiceType.SCHOOL: {
        #                 (CalendarDayEntry)
        #             },
        #             ServiceType.COLLECTION: {
        #                 (CalendarDayEntry)
        #             }
        #         }
        #     }
        # }

        days_ahead_calendar = {}

        # Iterate through 8 days, starting with yesterday and ending a week from today.
        for date_delta in list(range(-1, 7)):

            # Generate date from delta
            i_date = date_mod(date_delta)

            services_on_date: dict = {}

            # Get each service from response dictionary.
            for service_type in ServiceType:
                services_on_date[service_type] = resp_dict[i_date][service_type]

            days_ahead_calendar[date_delta] = {
                "date": i_date,
                "services": services_on_date,
            }

        log.debug("Built days ahead.")

        return days_ahead_calendar

    @classmethod
    def __build_next_exceptions(cls, resp_dict: dict) -> dict:
        """Build dict of next exception for all known types."""

        # Dictionary Format
        # {
        #   "2022-05-19": {
        #       ServiceType.PARKING: {
        #           (CalendarDayEntry)
        #       },
        #       ServiceType.SCHOOL: {
        #           (CalendarDayEntry)
        #       },
        #       ServiceType.COLLECTION: {
        #           (CalendarDayEntry)
        #       }
        #   }
        # }

        next_exceptions: dict = {}

        for date_, services in sorted(resp_dict.items()):

            # We don't want to show yesterday's calendar event as a next exception. Skip over if date is yesterday.
            if date_ == (today() - timedelta(days=1)):
                continue

            service_type: ServiceType
            service_entry: CalendarDayEntry

            for service_type, service_entry in services.items():

                # Skip if we already logged an exception for this category or if the status is not exceptional.
                if next_exceptions.get(service_type) or (
                    service_entry.status_profile
                    and service_entry.status_profile.standardized_type
                    in [
                        Service.StandardizedStatusType.NORMAL_ACTIVE,
                        Service.StandardizedStatusType.NORMAL_SUSPENDED,
                    ]
                ):
                    continue

                next_exceptions[service_type] = service_entry

        log.debug("Built next exceptions.")

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
                log.debug("got %s", resp_json)

        except aiohttp.ClientResponseError as error:
            if error.status in range(400, 500):
                raise self.InvalidAuth from error

            raise self.CannotConnect from error
        except Exception as error:
            raise self.CannotConnect from error

        log.debug("Called API.")

        return dict(resp_json)

    class UnexpectedEntry(Exception):
        """Thrown when API returns unexpected "key"."""

    class DateOrderException(Exception):
        """Thrown when iterable that is expected to be sorted by date is not."""

    class CannotConnect(Exception):
        """Thrown when server is unreachable."""

    class InvalidAuth(Exception):
        """Thrown when login fails."""
