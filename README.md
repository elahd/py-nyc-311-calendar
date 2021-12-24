# nyc311calendar

## Asynchronous data fetcher for NYC school closures, trash collection holidays, and alternate side parking suspensions.

Uses the [NYC 311 Public API](https://api-portal.nyc.gov/docs/services/nyc-311-public-api/operations/api-GetCalendar-get/console). Built to drive a Home Assistant add-in.

## Warning
This is an alpha release. Expect breaking changes.

I take no responsibility for parking tickets, overflowing trash cans, kids stranded at bus stops or missing exams, etc. 🤷🏼‍♂️

Use at your own risk.

## Usage

### First, get an API key

An NYC API Portal developer account is required to use this library.

1. Sign up at https://api-portal.nyc.gov/signup/.
2. Log in, then subscribe to the "NYC 311 Public Developers" product at https://api-portal.nyc.gov/products?api=nyc-311-public-api. This subscription unlocks the calendar product.
3. Get your API key at https://api-portal.nyc.gov/developer. Either key (primary/secondary) will work.

### Then, get data

```python

# Import library
from nyc311calendar.api import NYC311API

# Instantiate class
calendar = NYC311API(session, API_KEY)

# Fetch calendar
resp = await calendar.get_calendar()

```

### Constants

This library converts strings in the source API to constants wherever sensible and uses these constants everywhere (even as dictionary keys). That is, `"status": "CLOSED"` in the source API is represented as `'status_id': <Status.CLOSED: 7>}` in this library, where Status is an enum in the CivCalNYC class.

Constants are defined for:

1. Public Services in `CivCalNYC.ServiceType`.
2. Service Statuses in `CivCalNYC.Status`.
3. Calendar Types in `CivCalNYC.CalendarTypes`. See below for more info on calendar types.

### Calendar Types

CivCalNYC can return data in several formats, each defined in `CivCalNYC.CalendarTypes`:

#### By Date

The By Date calendar type returns all statuses for all services for 90 days starting on the day before the API request was made. The response dict is keyed by calendar date. This is essentially a constant-ized dump from the source API. The example below is truncated to save space, showing two of 90 days.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[NYC311API.CalendarTypes.BY_DATE], scrub=True
    )

```

```python

{<CalendarTypes.BY_DATE: 1>: datetime.date(2021, 12, 31): {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                                       'status_id': <Status.SUSPENDED: 6>,
                                                                                       'status_name': 'Suspended',
                                                                                       'description': "Alternate side parking and meters are suspended for New Year's Day (Observed).",
                                                                                       'exception_reason': "New Year's Day",
                                                                                       'exception_name': 'Rule Suspension',
                                                                                       'is_exception': True,
                                                                                       'routine_closure': False},
                                                            <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                                                     'status_id': <Status.ON_SCHEDULE: 2>,
                                                                                     'status_name': 'On Schedule',
                                                                                     'description': 'Trash and recycling collections are on schedule. Compost collections in participating neighborhoods are also on schedule.',
                                                                                     'exception_reason': '',
                                                                                     'exception_name': 'Collection Change',
                                                                                     'is_exception': False,
                                                                                     'routine_closure': False},
                                                            <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                                      'status_id': <Status.CLOSED: 7>,
                                                                                      'status_name': 'Closed',
                                                                                      'description': 'Public schools are closed for Winter Recess. Students return Monday.',
                                                                                      'exception_reason': 'Winter Recess Last Day',
                                                                                      'exception_name': 'Closure',
                                                                                      'is_exception': True,
                                                                                      'routine_closure': False}},
                              datetime.date(2022, 1, 1): {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                                     'status_id': <Status.SUSPENDED: 6>,
                                                                                     'status_name': 'Suspended',
                                                                                     'description': "Alternate side parking and meters are suspended for New Year's Day.",
                                                                                     'exception_reason': "New Year's Day",
                                                                                     'exception_name': 'Rule Suspension',
                                                                                     'is_exception': True,
                                                                                     'routine_closure': False},
                                                          <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                                                   'status_id': <Status.SUSPENDED: 6>,
                                                                                   'status_name': 'Suspended',
                                                                                   'description': "Trash, recycling, and compost collections are suspended for New Year's Day.",
                                                                                   'exception_reason': "New Year's Day",
                                                                                   'exception_name': 'Collection Change',
                                                                                   'is_exception': True,
                                                                                   'routine_closure': False},
                                                          <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                                    'status_id': <Status.NOT_IN_SESSION: 5>,
                                                                                    'status_name': 'Not In Effect',
                                                                                    'description': 'Public schools are not in session.',
                                                                                    'exception_reason': '',
                                                                                    'exception_name': 'Closure',
                                                                                    'is_exception': False,
                                                                                    'routine_closure': True}}}}

```

#### Days Ahead

The Days Ahead calendar type returns all statuses for all services for 8 days starting on the day before the API request was made. The response dict is keyed by number of days relative to today. This is useful for showing a calendar of the week ahead (and yesterday, just in case you forgot to move your car). The example below is truncated to save space, showing three of 90 days.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[NYC311API.CalendarTypes.DAYS_AHEAD], scrub=True
    )

```

```python

{<CalendarTypes.DAYS_AHEAD: 2>: {-1: {'date': datetime.date(2021, 12, 23),
                                      'services': {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                              'status_id': <Status.IN_EFFECT: 1>,
                                                                              'status_name': 'In Effect',
                                                                              'description': 'Alternate side parking and meters are in effect. Follow the new rule for residential streets: If the ASP sign shows more than one day, only the last day is in effect for that side of the street.',
                                                                              'exception_reason': '',
                                                                              'exception_name': 'Rule Suspension',
                                                                              'is_exception': False,
                                                                              'routine_closure': False},
                                                   <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                                            'status_id': <Status.ON_SCHEDULE: 2>,
                                                                            'status_name': 'On Schedule',
                                                                            'description': 'Trash and recycling collections are on schedule. Compost collections in participating neighborhoods are also on schedule.',
                                                                            'exception_reason': '',
                                                                            'exception_name': 'Collection Change',
                                                                            'is_exception': False,
                                                                            'routine_closure': False},
                                                   <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                             'status_id': <Status.OPEN: 3>,
                                                                             'status_name': 'Open',
                                                                             'description': 'Public schools are open.',
                                                                             'exception_reason': '',
                                                                             'exception_name': 'Closure',
                                                                             'is_exception': False,
                                                                             'routine_closure': False}}},
                                 0: {'date': datetime.date(2021, 12, 24),
                                     'services': {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                             'status_id': <Status.SUSPENDED: 6>,
                                                                             'status_name': 'Suspended',
                                                                             'description': 'Alternate side parking and meters are suspended for Christmas Day (Observed).',
                                                                             'exception_reason': 'Christmas Day',
                                                                             'exception_name': 'Rule Suspension',
                                                                             'is_exception': True,
                                                                             'routine_closure': False},
                                                  <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                                           'status_id': <Status.ON_SCHEDULE: 2>,
                                                                           'status_name': 'On Schedule',
                                                                           'description': 'Trash and recycling collections are on schedule. Compost collections in participating neighborhoods are also on schedule.',
                                                                           'exception_reason': '',
                                                                           'exception_name': 'Collection Change',
                                                                           'is_exception': False,
                                                                           'routine_closure': False},
                                                  <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                            'status_id': <Status.CLOSED: 7>,
                                                                            'status_name': 'Closed',
                                                                            'description': 'Public schools are closed for Winter Recess through December 31.',
                                                                            'exception_reason': 'Winter Recess',
                                                                            'exception_name': 'Closure',
                                                                            'is_exception': True,
                                                                            'routine_closure': False}}},
                                 1: {'date': datetime.date(2021, 12, 25),
                                     'services': {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                             'status_id': <Status.SUSPENDED: 6>,
                                                                             'status_name': 'Suspended',
                                                                             'description': 'Alternate side parking and meters are suspended for Christmas.',
                                                                             'exception_reason': 'Christmas',
                                                                             'exception_name': 'Rule Suspension',
                                                                             'is_exception': True,
                                                                             'routine_closure': False},
                                                  <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                                           'status_id': <Status.SUSPENDED: 6>,
                                                                           'status_name': 'Suspended',
                                                                           'description': 'Trash, recycling, and compost collections are suspended for Christmas.',
                                                                           'exception_reason': 'Christmas',
                                                                           'exception_name': 'Collection Change',
                                                                           'is_exception': True,
                                                                           'routine_closure': False},
                                                  <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                            'status_id': <Status.CLOSED: 7>,
                                                                            'status_name': 'Closed',
                                                                            'description': 'Public schools are closed for Winter Recess through December 31.',
                                                                            'exception_reason': 'Winter Recess',
                                                                            'exception_name': 'Closure',
                                                                            'is_exception': True,
                                                                            'routine_closure': False}}}}}

```

#### Next Exceptions

The Next Exceptions calendar type returns the next date on which there is a service exception for either of the three covered services. The response dict is keyed by service type. This is useful when you're not interested in normal operations and only want to know, say, when the next school closure is. The example below shows the full response.

Note that exceptions include things like holidays, snow days, half days, and winter break. Summer session will not show up as an exception.

```python

async with aiohttp.ClientSession() as session:
    calendar = NYC311API(session, API_KEY)
    resp = await calendar.get_calendar(
        calendars=[NYC311API.CalendarTypes.NEXT_EXCEPTIONS], scrub=True
    )

```

```python

{<CalendarTypes.NEXT_EXCEPTIONS: 3>: {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                 'status_id': <Status.SUSPENDED: 6>,
                                                                 'status_name': 'Suspended',
                                                                 'description': 'Alternate side parking and meters are suspended for Christmas Day (Observed).',
                                                                 'exception_reason': 'Christmas Day',
                                                                 'exception_name': 'Rule Suspension',
                                                                 'is_exception': True,
                                                                 'routine_closure': False,
                                                                 'date': datetime.date(2021, 12, 24)},
                                      <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                'status_id': <Status.CLOSED: 7>,
                                                                'status_name': 'Closed',
                                                                'description': 'Public schools are closed for Winter Recess through December 31.',
                                                                'exception_reason': 'Winter Recess',
                                                                'exception_name': 'Closure',
                                                                'is_exception': True,
                                                                'routine_closure': False,
                                                                'date': datetime.date(2021, 12, 24)},
                                      <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                               'status_id': <Status.SUSPENDED: 6>,
                                                               'status_name': 'Suspended',
                                                               'description': 'Trash, recycling, and compost collections are suspended for Christmas.',
                                                               'exception_reason': 'Christmas',
                                                               'exception_name': 'Collection Change',
                                                               'is_exception': True,
                                                               'routine_closure': False,
                                                               'date': datetime.date(2021, 12, 25)}}}

```

## Example

### This code

```python

from datetime import date
import asyncio
import aiohttp
from nyc311calendar.api import NYC311API
import pprint

API_KEY = "YOUR_API_KEY_HERE"

pp = pprint.PrettyPrinter(width=200, sort_dicts=False)


async def main():
    async with aiohttp.ClientSession() as session:
        calendar = NYC311API(session, API_KEY)
        resp = await calendar.get_calendar(
            calendars=[NYC311API.CalendarTypes.NEXT_EXCEPTIONS], scrub=True
        )
        pp.pprint(resp)

    await session.close()


asyncio.run(main())

```

### Returns this result

```python

{<CalendarTypes.NEXT_EXCEPTIONS: 3>: {<ServiceType.PARKING: 1>: {'service_name': 'Alternate Side Parking',
                                                                 'status_id': <Status.SUSPENDED: 6>,
                                                                 'status_name': 'Suspended',
                                                                 'description': 'Alternate side parking and meters are suspended for Christmas Day (Observed).',
                                                                 'exception_reason': 'Christmas Day',
                                                                 'exception_name': 'Rule Suspension',
                                                                 'is_exception': True,
                                                                 'routine_closure': False,
                                                                 'date': datetime.date(2021, 12, 24)},
                                      <ServiceType.SCHOOL: 2>: {'service_name': 'School',
                                                                'status_id': <Status.CLOSED: 7>,
                                                                'status_name': 'Closed',
                                                                'description': 'Public schools are closed for Winter Recess through December 31.',
                                                                'exception_reason': 'Winter Recess',
                                                                'exception_name': 'Closure',
                                                                'is_exception': True,
                                                                'routine_closure': False,
                                                                'date': datetime.date(2021, 12, 24)},
                                      <ServiceType.TRASH: 3>: {'service_name': 'Garbage and Recycling',
                                                               'status_id': <Status.SUSPENDED: 6>,
                                                               'status_name': 'Suspended',
                                                               'description': 'Trash, recycling, and compost collections are suspended for Christmas.',
                                                               'exception_reason': 'Christmas',
                                                               'exception_name': 'Collection Change',
                                                               'is_exception': True,
                                                               'routine_closure': False,
                                                               'date': datetime.date(2021, 12, 25)}}}

```
