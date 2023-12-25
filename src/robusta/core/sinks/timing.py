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
