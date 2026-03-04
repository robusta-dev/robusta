from abc import ABC
from datetime import datetime
from typing import List, Tuple

import pytz

from robusta.core.model.env_vars import DEFAULT_TIMEZONE


_DAY_STR_TO_NUM = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THR": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6,
}

DAY_NAMES = list(_DAY_STR_TO_NUM.keys())


class TimeSliceBase(ABC):
    def is_active_now(self) -> bool:
        raise NotImplementedError()


class TimeSlice(TimeSliceBase):
    def __init__(self, days: List[str], time_intervals: List[Tuple[str, str]] = [], timezone=DEFAULT_TIMEZONE):
        self.days = [self._parse_day(day) for day in days]
        self.time_intervals = [(self._parse_time(start), self._parse_time(end)) for start, end in time_intervals]
        try:
            self.timezone = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown time zone {timezone}")

    def _parse_day(self, day_str: str) -> int:
        try:
            return _DAY_STR_TO_NUM[day_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid day of the week: {day_str}")

    def _parse_time(self, time_str: str) -> int:
        # Return the time represented by time_str (for example "13:22") as a number
        # of seconds since midnight.
        hr, min = time_str.strip().split(":")
        hr = int(hr)
        min = int(min)
        if not (0 <= hr <= 23 and 0 <= min <= 59):
            raise ValueError(f"Invalid time: {time_str}")
        return hr * 3600 + min * 60

    def is_active_now(self) -> bool:
        tznow = datetime.now(self.timezone)
        tz_second_of_day = 3600 * tznow.hour + 60 * tznow.minute + tznow.second
        if self.time_intervals:
            return tznow.weekday() in self.days and any(
                start <= tz_second_of_day <= end for (start, end) in self.time_intervals
            )
        else:
            # time_intervals not set, assume the whole day is acceptable
            return tznow.weekday() in self.days


class TimeSliceAlways(TimeSliceBase):
    def is_active_now(self) -> bool:
        return True


class MuteDateInterval:
    """Checks if the current date/time falls within a mute interval.

    start_date and end_date are in MM-DD HH:MM format (no year).
    The interval applies to the current year. If start_date > end_date
    (e.g. 12-20 to 01-05), it wraps across the year boundary.
    """

    def __init__(self, start_date: str, end_date: str, timezone: str = "UTC"):
        self.start_month, self.start_day, self.start_hour, self.start_minute = self._parse(start_date)
        self.end_month, self.end_day, self.end_hour, self.end_minute = self._parse(end_date)
        try:
            self.timezone = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown time zone {timezone}")

    def _parse(self, date_str: str) -> Tuple[int, int, int, int]:
        date_part, time_part = date_str.strip().split(" ")
        month, day = date_part.split("-")
        hour, minute = time_part.split(":")
        return int(month), int(day), int(hour), int(minute)

    def _to_tuple(self, month: int, day: int, hour: int, minute: int) -> Tuple[int, int, int, int]:
        return (month, day, hour, minute)

    def is_muted_now(self) -> bool:
        now = datetime.now(self.timezone)
        current = self._to_tuple(now.month, now.day, now.hour, now.minute)
        start = self._to_tuple(self.start_month, self.start_day, self.start_hour, self.start_minute)
        end = self._to_tuple(self.end_month, self.end_day, self.end_hour, self.end_minute)

        if start <= end:
            return start <= current <= end
        else:
            # Wraps across year boundary (e.g. 12-20 00:00 to 01-05 00:00)
            return current >= start or current <= end
