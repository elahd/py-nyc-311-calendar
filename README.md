[![Downloads](https://pepy.tech/badge/nyc311calendar)](https://pepy.tech/project/nyc311calendar)

# nyc311calendar

## Asynchronous data fetcher for NYC school closures, trash collection holidays, and alternate side parking suspensions.

Uses the [NYC 311 Public API](https://api-portal.nyc.gov/docs/services/nyc-311-public-api/operations/api-GetCalendar-get/console). Built to drive the Home Assistant [NYC 311 Public Services Calendar](https://github.com/elahd/ha-nyc311) add-in.

## Warning

This is an alpha release. Expect breaking changes.

I take no responsibility for parking tickets, overflowing trash cans, kids stranded at bus stops or missing exams, etc. 🤷🏼‍♂️

Use at your own risk.

## Usage

### First, install via pip

```bash
pip install nyc311calendar
```

### Then, get an API key

An NYC API Portal developer account is required to use this library.

1. Sign up at https://api-portal.nyc.gov/signup/.
2. Log in, then subscribe to the "NYC 311 Public Developers" product at https://api-portal.nyc.gov/products?api=nyc-311-public-api. This subscription unlocks the calendar product.
3. Get your API key at https://api-portal.nyc.gov/developer. Either key (primary/secondary) will work.

### Finally, get data

```python

# Import modules
from nyc311calendar import CalendarType, NYC311API

# Instantiate class
calendar = NYC311API(session, API_KEY)

# Fetch calendar
resp = await calendar.get_calendar()

```

There's more to this. You'll need to provide an aiohttp ClientSession object. See the examples folder for guidance.

### Constants

This library converts strings in the source API to constants wherever sensible and uses these constants everywhere (even as dictionary keys). That is, `"status": "CLOSED"` in the source API is represented as `'status_id': <Status.CLOSED: 7>}` in this library, where Status is an enum in the CivCalNYC class.

Constants are defined for:

1. Public services in `services.ServiceType`.
2. Service statuses in `services.StandardizedStatusTypes`. The source API is a mess of poorly named statuses. The StandardizedStatusTypes attempts to make sense of the underlying statuses.
3. Calendar types in `CalendarType`. See below for more info on calendar types.

### Calendar Day Entries

Data for each calendar day is returned in a `CalendarDayEntry` dataclass.

### Calendar Types

nyc311calendar can return data in several formats, each defined in the `CalendarType` enum:

#### By Date

The By Date calendar type returns all statuses for all services for 90 days starting on the day before the API request was made. The response dict is keyed by calendar date. This is essentially a constant-ized dump from the source API. The example below is truncated to save space, showing two of 90 days.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[CalendarType.BY_DATE], scrub=True
    )

```

```python
{
    <CalendarType.BY_DATE: 1>: 
        datetime.date(2021, 12, 31): {
            <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
            <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
            <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
        },
        datetime.date(2022, 1, 1): {
            <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
            <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
            <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
        }
}
```

#### Days Ahead

The Days Ahead calendar type returns all statuses for all services for 8 days starting on the day before the API request was made. The response dict is keyed by number of days relative to today. This is useful for showing a calendar of the week ahead (and yesterday, just in case you forgot to move your car). The example below is truncated to save space, showing three of 90 days.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[CalendarType.DAYS_AHEAD], scrub=True
    )

```

```python
{
    <CalendarTypes.DAYS_AHEAD: 2>: {
        -1: {
            'date': datetime.date(2021, 12, 23),
            'services': {
                <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
                <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
                <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
        },
        0: {
            'date': datetime.date(2021, 12, 24),
            'services': {
                <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
                <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
                <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
        },
        1: {
            'date': datetime.date(2021, 12, 25),
            'services': {
                <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
                <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
                <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
        }
    }
}
```

#### Next Exceptions

The Next Exceptions calendar type returns the next date on which there is a service exception for either of the three covered services. The response dict is keyed by service type. This is useful when you're not interested in normal operations and only want to know, say, when the next school closure is. The example below shows the full response.

Note that exceptions include things like holidays, snow days, half days, and winter break.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[CalendarType.NEXT_EXCEPTIONS], scrub=True
    )

```

```python
{
    <CalendarTypes.NEXT_EXCEPTIONS: 3>: {
        <ServiceType.PARKING: "Alternate Side Parking">: CalendarDayEntry(...),
        <ServiceType.SCHOOL: "Schools">: CalendarDayEntry(...),
        <ServiceType.SANITATION: "Collections">: CalendarDayEntry(...)
    }
}
```
