"""Services and their attributes."""
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum


class ServiceType(Enum):
    """Types of events reported via API."""

    # Values represent keys provided by API. Do not change.

    PARKING = "Alternate Side Parking"
    SCHOOL = "Schools"
    SANITATION = "Collections"


@dataclass
class StatusTypeDetail:
    """Status impact on a particular ServiceType."""

    name: str
    exception_type: School.StandardizedExceptionType | Parking.StandardizedExceptionType | Sanitation.StandardizedExceptionType
    description: str


class Service(ABC):
    """Abstract class for real city services."""

    status_map: dict

    @abstractmethod
    class StatusType(Enum):
        """Calendar item status codes."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Service name."""

    @property
    @abstractmethod
    def exception_name(self) -> str:
        """Term for when this service is suspended."""

    class StandardizedExceptionType(Enum):
        """Calendar views."""

        NORMAL_ACTIVE = 1  # E.g.: School open; garbage to be collected; parking meters and asp in effect.
        NORMAL_SUSPENDED = 2  # E.g.: School closed on weekends; no garbage on Sunday; no meters on Sunday.
        SUSPENDED = 3  # E.g.: Service change for holiday.
        DELAYED = 4  # E.g.: Snow delay.
        PARTIAL = 5  # E.g.: School open for teachers only; compost canceled but trash/recycling still on.
        UNSURE = 6  # E.g.: Service may or may not be normal.
        RECESS = 7  # Summer recess. (School Only)
        REMOTE = 99  # COVID-19 remote protocols in effect. (School Only)


class School(Service):
    """Public schools."""

    class StatusType(Enum):
        """Calendar item status codes."""

        # Keys match API source. Do not change unless API changes.

        CLOSED = "CLOSED"
        NO_INFO = "NO INFORMATION"
        NOT_IN_SESSION = "NOT IN SESSION"
        OPEN = "OPEN"
        PARTLY_OPEN = "PARTLY OPEN"
        REMOTE_ONLY = "REMOTE ONLY"
        STAFF_ONLY = "STAFF ONLY"
        TENTATIVE = "TENTATIVE"

    status_map: dict = {
        StatusType.CLOSED: StatusTypeDetail(
            name="Closed",
            exception_type=Service.StandardizedExceptionType.SUSPENDED,
            description="School is closed for the summer.",
        ),
        StatusType.NO_INFO: StatusTypeDetail(
            name="No Information",
            exception_type=Service.StandardizedExceptionType.UNSURE,
            description="Information is not available for this date.",
        ),
        StatusType.NOT_IN_SESSION: StatusTypeDetail(
            name="Not In Session",
            exception_type=Service.StandardizedExceptionType.SUSPENDED,
            description="Schools are closed.",
        ),
        StatusType.OPEN: StatusTypeDetail(
            name="Open",
            exception_type=Service.StandardizedExceptionType.NORMAL_ACTIVE,
            description="School is open as usual.",
        ),
        StatusType.PARTLY_OPEN: StatusTypeDetail(
            name="Partly Open",
            exception_type=Service.StandardizedExceptionType.PARTIAL,
            description="School is open for some students and not others.",
        ),
        StatusType.REMOTE_ONLY: StatusTypeDetail(
            name="Remote Only",
            exception_type=Service.StandardizedExceptionType.REMOTE,
            description="Students are scheduled for remote learning.",
        ),
        StatusType.STAFF_ONLY: StatusTypeDetail(
            name="Closed for Students",
            exception_type=Service.StandardizedExceptionType.PARTIAL,
            description="Schools are closed for students but open for staff.",
        ),
        StatusType.TENTATIVE: StatusTypeDetail(
            name="Tentative",
            exception_type=Service.StandardizedExceptionType.UNSURE,
            description="Schedule for this day has not yet been determined.",
        ),
    }

    @property
    def name(self) -> str:
        """Service name."""

        return "School"

    @property
    def exception_name(self) -> str:
        """Term for when this service is suspended."""

        return "Closure"


class Sanitation(Service):
    """Trash, recycling, and compost collections."""

    class StatusType(Enum):
        """Calendar item status codes."""

        # Keys match API source. Do not change unless API changes.

        NO_COMPOST = "COMPOST SUSPENDED"
        DELAYED = "DELAYED"
        NO_INFO = "NO INFORMATION"
        NOT_IN_EFFECT = "NOT IN EFFECT"
        ON_SCHEDULE = "ON SCHEDULE"
        SUSPENDED = "SUSPENDED"
        NO_LEGACY_TRASH = "COLLECTION AND RECYCLING SUSPENDED"

    status_map: dict = {
        StatusType.NO_COMPOST: StatusTypeDetail(
            name="Compost Collection Suspended",
            exception_type=Service.StandardizedExceptionType.PARTIAL,
            description=(
                "Compost collection is suspended. Trash and recycling collections"
                " are on schedule."
            ),
        ),
        StatusType.DELAYED: StatusTypeDetail(
            name="Delayed",
            exception_type=Service.StandardizedExceptionType.DELAYED,
            description="Trash, recycling, and compost collections are delayed.",
        ),
        StatusType.NO_INFO: StatusTypeDetail(
            name="To Be Determined",
            exception_type=Service.StandardizedExceptionType.UNSURE,
            description="Schedule for this day has not yet been determined.",
        ),
        StatusType.NOT_IN_EFFECT: StatusTypeDetail(
            name="Not In Effect",
            exception_type=Service.StandardizedExceptionType.NORMAL_SUSPENDED,
            description=(
                "Trash, recycling, and compost collections are not in effect on"
                " Sundays."
            ),
        ),
        StatusType.ON_SCHEDULE: StatusTypeDetail(
            name="On Schedule",
            exception_type=Service.StandardizedExceptionType.NORMAL_ACTIVE,
            description=(
                "Trash, recycling, and compost collection are operating as usual."
            ),
        ),
        StatusType.SUSPENDED: StatusTypeDetail(
            name="Suspended",
            exception_type=Service.StandardizedExceptionType.SUSPENDED,
            description="Trash, recycling, and compost collections are suspended.",
        ),
        StatusType.NO_LEGACY_TRASH: StatusTypeDetail(
            name="Trash and Recycling Collection Suspended",
            exception_type=Service.StandardizedExceptionType.PARTIAL,
            description=(
                "Trash and recycling collections are suspended. Compost collection"
                " is on schedule."
            ),
        ),
    }

    @property
    def name(self) -> str:
        """Service name."""

        return "Sanitation"

    @property
    def exception_name(self) -> str:
        """Term for when this service is suspended."""

        return "Collection Suspension"


class Parking(Service):
    """Alternate side parking & meters."""

    class StatusType(Enum):
        """Calendar item status codes."""

        # Keys match API source. Do not change unless API changes.

        IN_EFFECT = "IN EFFECT"
        NO_INFO = "NO INFORMATION"
        NOT_IN_EFFECT = "NOT IN EFFECT"
        SUSPENDED = "SUSPENDED"

    status_map = {
        StatusType.IN_EFFECT: StatusTypeDetail(
            name="In Effect",
            exception_type=Service.StandardizedExceptionType.NORMAL_ACTIVE,
            description="Alternate side parking and meters are in effect.",
        ),
        StatusType.NO_INFO: StatusTypeDetail(
            name="No Information",
            exception_type=Service.StandardizedExceptionType.UNSURE,
            description="Information is not available for this date.",
        ),
        StatusType.NOT_IN_EFFECT: StatusTypeDetail(
            name="Not In Effect",
            exception_type=Service.StandardizedExceptionType.NORMAL_SUSPENDED,
            description=(
                "Alternate side parking and meters are not in effect on Sundays."
            ),
        ),
        StatusType.SUSPENDED: StatusTypeDetail(
            name="Suspended",
            exception_type=Service.StandardizedExceptionType.SUSPENDED,
            description="Alternate side parking and meters are suspended.",
        ),
    }

    @property
    def name(self) -> str:
        """Service name."""

        return "Parking"

    @property
    def exception_name(self) -> str:
        """Term for when this service is suspended."""

        return "Rule Suspension"
