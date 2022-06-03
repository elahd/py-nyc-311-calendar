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
class ServiceTypeProfile:
    """Service metadata."""

    name: str  # Service name.
    exception_name: str  # Term for when this service is suspended.
    exception_title_name: str
    service_type: ServiceType
    status_strings: dict


@dataclass
class StatusTypeProfile:
    """Status impact on a particular ServiceType."""

    name: str
    description: str
    standardized_type: School.StandardizedStatusType | Parking.StandardizedStatusType | Sanitation.StandardizedStatusType
    reported_type: School.StatusType | Parking.StatusType | Sanitation.StatusType


class Service(ABC):
    """Abstract class for real city services."""

    @abstractmethod
    class StatusType(Enum):
        """Calendar item status codes."""

    PROFILE: ServiceTypeProfile

    STATUS_MAP: dict

    class StandardizedStatusType(Enum):
        """Calendar views."""

        NORMAL_ACTIVE = 1  # E.g.: School open; garbage to be collected; parking meters and asp in effect.
        NORMAL_SUSPENDED = 2  # E.g.: School closed on weekends; no garbage on Sunday; no meters on Sunday.
        SUSPENDED = 3  # E.g.: Service change for holiday.
        DELAYED = 4  # E.g.: Snow delay.
        PARTIAL = 5  # E.g.: School open for some students and not others; compost canceled but trash/recycling still on.
        UNSURE = 6  # E.g.: Service may or may not be normal.
        RECESS = 7  # Summer recess. (School Only)
        STAFF_ONLY = 8  # E.g.: School open for teachers only. (School only)
        LAST_DAY = 98  # School is open for the last day of the year. (School only)
        REMOTE = 99  # COVID-19 remote protocols in effect. (School Only)

    STATUS_STRINGS = {
        StandardizedStatusType.NORMAL_ACTIVE: "Open",
        StandardizedStatusType.NORMAL_SUSPENDED: "Closed",
        StandardizedStatusType.SUSPENDED: "Suspended",
        StandardizedStatusType.DELAYED: "Delayed",
        StandardizedStatusType.PARTIAL: "Partially Closed",
        StandardizedStatusType.UNSURE: "TBD",
        StandardizedStatusType.RECESS: "in Recess",
        StandardizedStatusType.REMOTE: "Remote Learning",
        StandardizedStatusType.STAFF_ONLY: "Closed for Students",
        StandardizedStatusType.LAST_DAY: "Last Day",
    }


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

    STATUS_STRINGS = Service.STATUS_STRINGS | {
        Service.StandardizedStatusType.SUSPENDED: "Closed"
    }

    PROFILE = ServiceTypeProfile(
        name="School",
        exception_name="Closure",
        exception_title_name="Schools",
        service_type=ServiceType.SCHOOL,
        status_strings=STATUS_STRINGS,
    )

    STATUS_MAP: dict = {
        StatusType.CLOSED: StatusTypeProfile(
            name="Closed",
            standardized_type=Service.StandardizedStatusType.SUSPENDED,
            description="School is closed for a holiday or special event.",
            reported_type=StatusType.CLOSED,
        ),
        StatusType.NO_INFO: StatusTypeProfile(
            name="No Information",
            standardized_type=Service.StandardizedStatusType.UNSURE,
            description="Information is not available for this date.",
            reported_type=StatusType.NO_INFO,
        ),
        StatusType.NOT_IN_SESSION: StatusTypeProfile(
            name="Not In Session",
            standardized_type=Service.StandardizedStatusType.NORMAL_SUSPENDED,
            description="Schools are closed for the weekend or for an extended break.",
            reported_type=StatusType.NOT_IN_SESSION,
        ),
        StatusType.OPEN: StatusTypeProfile(
            name="Open",
            standardized_type=Service.StandardizedStatusType.NORMAL_ACTIVE,
            description="School is open as usual.",
            reported_type=StatusType.OPEN,
        ),
        StatusType.PARTLY_OPEN: StatusTypeProfile(
            name="Partly Open",
            standardized_type=Service.StandardizedStatusType.PARTIAL,
            description="School is open for some students and not others.",
            reported_type=StatusType.PARTLY_OPEN,
        ),
        StatusType.REMOTE_ONLY: StatusTypeProfile(
            name="Remote Only",
            standardized_type=Service.StandardizedStatusType.REMOTE,
            description="Students are scheduled for remote learning.",
            reported_type=StatusType.REMOTE_ONLY,
        ),
        StatusType.STAFF_ONLY: StatusTypeProfile(
            name="Closed for Students",
            standardized_type=Service.StandardizedStatusType.PARTIAL,
            description="Schools are closed for students but open for staff.",
            reported_type=StatusType.STAFF_ONLY,
        ),
        StatusType.TENTATIVE: StatusTypeProfile(
            name="Tentative",
            standardized_type=Service.StandardizedStatusType.UNSURE,
            description="Schedule for this day has not yet been determined.",
            reported_type=StatusType.TENTATIVE,
        ),
    }


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

    PROFILE = ServiceTypeProfile(
        name="Sanitation",
        exception_name="Collection Suspension",
        exception_title_name="Sanitation Collection",
        service_type=ServiceType.SANITATION,
        status_strings=Service.STATUS_STRINGS,
    )

    STATUS_MAP: dict = {
        StatusType.NO_COMPOST: StatusTypeProfile(
            name="Compost Collection Suspended",
            standardized_type=Service.StandardizedStatusType.PARTIAL,
            description=(
                "Compost collection is suspended. Trash and recycling collections"
                " are on schedule."
            ),
            reported_type=StatusType.NO_COMPOST,
        ),
        StatusType.DELAYED: StatusTypeProfile(
            name="Delayed",
            standardized_type=Service.StandardizedStatusType.DELAYED,
            description="Trash, recycling, and compost collections are delayed.",
            reported_type=StatusType.DELAYED,
        ),
        StatusType.NO_INFO: StatusTypeProfile(
            name="To Be Determined",
            standardized_type=Service.StandardizedStatusType.UNSURE,
            description="Schedule for this day has not yet been determined.",
            reported_type=StatusType.NO_INFO,
        ),
        StatusType.NOT_IN_EFFECT: StatusTypeProfile(
            name="Not In Effect",
            standardized_type=Service.StandardizedStatusType.NORMAL_SUSPENDED,
            description=(
                "Trash, recycling, and compost collections are not in effect on"
                " Sundays."
            ),
            reported_type=StatusType.NOT_IN_EFFECT,
        ),
        StatusType.ON_SCHEDULE: StatusTypeProfile(
            name="On Schedule",
            standardized_type=Service.StandardizedStatusType.NORMAL_ACTIVE,
            description=(
                "Trash, recycling, and compost collection are operating as usual."
            ),
            reported_type=StatusType.ON_SCHEDULE,
        ),
        StatusType.SUSPENDED: StatusTypeProfile(
            name="Suspended",
            standardized_type=Service.StandardizedStatusType.SUSPENDED,
            description="Trash, recycling, and compost collections are suspended.",
            reported_type=StatusType.SUSPENDED,
        ),
        StatusType.NO_LEGACY_TRASH: StatusTypeProfile(
            name="Trash and Recycling Collection Suspended",
            standardized_type=Service.StandardizedStatusType.PARTIAL,
            description=(
                "Trash and recycling collections are suspended. Compost collection"
                " is on schedule."
            ),
            reported_type=StatusType.NO_LEGACY_TRASH,
        ),
    }


class Parking(Service):
    """Alternate side parking & meters."""

    class StatusType(Enum):
        """Calendar item status codes."""

        # Keys match API source. Do not change unless API changes.

        IN_EFFECT = "IN EFFECT"
        NO_INFO = "NO INFORMATION"
        NOT_IN_EFFECT = "NOT IN EFFECT"
        SUSPENDED = "SUSPENDED"

    PROFILE = ServiceTypeProfile(
        name="Parking",
        exception_name="Rule Suspension",
        exception_title_name="Parking Rules",
        service_type=ServiceType.PARKING,
        status_strings=Service.STATUS_STRINGS,
    )

    STATUS_MAP = {
        StatusType.IN_EFFECT: StatusTypeProfile(
            name="In Effect",
            standardized_type=Service.StandardizedStatusType.NORMAL_ACTIVE,
            description="Alternate side parking and meters are in effect.",
            reported_type=StatusType.IN_EFFECT,
        ),
        StatusType.NO_INFO: StatusTypeProfile(
            name="No Information",
            standardized_type=Service.StandardizedStatusType.UNSURE,
            description="Information is not available for this date.",
            reported_type=StatusType.NO_INFO,
        ),
        StatusType.NOT_IN_EFFECT: StatusTypeProfile(
            name="Not In Effect",
            standardized_type=Service.StandardizedStatusType.NORMAL_SUSPENDED,
            description=(
                "Alternate side parking and meters are not in effect on Sundays."
            ),
            reported_type=StatusType.NOT_IN_EFFECT,
        ),
        StatusType.SUSPENDED: StatusTypeProfile(
            name="Suspended",
            standardized_type=Service.StandardizedStatusType.SUSPENDED,
            description="Alternate side parking and meters are suspended.",
            reported_type=StatusType.SUSPENDED,
        ),
    }
