import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, root_validator, validator
from pydantic.types import PositiveInt
import pytz

from robusta.core.playbooks.playbook_utils import replace_env_vars_values
from robusta.core.sinks.timing import DAY_NAMES
from robusta.utils.scope import ScopeParams

TIME_RE = re.compile("^\d\d:\d\d$")


def check_time_format(value: str) -> str:
    if not TIME_RE.match(value):
        raise ValueError(f"invalid time: {value}")
    return value


class ActivityHours(BaseModel):
    start: str
    end: str

    _validator_start = validator("start", allow_reuse=True)(check_time_format)
    _validator_end = validator("end", allow_reuse=True)(check_time_format)


class ActivityInterval(BaseModel):
    days: List[str]
    hours: List[ActivityHours] = []

    @validator("days")
    def check_days(cls, value: List[str]):
        for day in value:
            if day.upper() not in DAY_NAMES:
                raise ValueError(f"invalid day name {day}")
        return value


class ActivityParams(BaseModel):
    timezone: str = "UTC"
    intervals: List[ActivityInterval]

    @validator("timezone")
    def check_timezone(cls, timezone: str):
        if timezone not in pytz.all_timezones:
            raise ValueError(f"unknown timezone {timezone}")
        return timezone

    @validator("intervals")
    def check_intervals(cls, intervals: List[ActivityInterval]):
        if not intervals:
            raise ValueError("at least one interval has to be specified for the activity settings")
        return intervals


class RegularNotificationModeParams(BaseModel):
    # This is mandatory because using the regular mode without setting it
    # would make no sense - all the notifications would just pass through
    # normally.
    ignore_first: PositiveInt


# a list of attribute names, which can be strings or dicts of the form
# {"labels": ["app", "label-xyz"]} etc.
GroupingAttributeSelectorListT = List[Union[str, Dict[str, List[str]]]]


class SummaryNotificationModeParams(BaseModel):
    threaded: bool = True
    by: GroupingAttributeSelectorListT = ["identifier"]


class NotificationModeParams(BaseModel):
    regular: Optional[RegularNotificationModeParams]
    summary: Optional[SummaryNotificationModeParams]
    # TODO should we enforce that only one of these is set?

    @root_validator
    def validate_exactly_one_defined(cls, values: Dict):
        if values.get("regular") and values.get("summary"):
            raise ValueError('"regular" and "summary" notification grouping modes must not be defined at the same time')
        if not (values.get("regular") or values.get("summary")):
            raise ValueError('either "regular" or "summary" notification grouping mode must be defined')
        return values


class GroupingParams(BaseModel):
    group_by: GroupingAttributeSelectorListT = ["cluster"]
    interval: int = 15*60  # in seconds
    notification_mode: Optional[NotificationModeParams]

    @root_validator
    def validate_notification_mode(cls, values: Dict):
        if values is None:
            return {"summary": SummaryNotificationModeParams()}
        return values


class SinkBaseParams(ABC, BaseModel):
    name: str
    send_svg: bool = False
    default: bool = True
    match: dict = {}
    scope: Optional[ScopeParams]
    activity: Optional[ActivityParams]
    grouping: Optional[GroupingParams]
    stop: bool = False  # Stop processing if this sink has been matched

    @root_validator
    def env_values_validation(cls, values: Dict):
        updated = replace_env_vars_values(values)
        match = updated.get("match", {})
        if match:
            labels = match.get("labels")
            if labels:
                match["labels"] = cls.__parse_dict_matchers(labels)
            annotations = match.get("annotations")
            if annotations:
                match["annotations"] = cls.__parse_dict_matchers(annotations)
        return updated

    @root_validator
    def validate_grouping(cls, values: Dict):
        if values.get("grouping") and not cls._supports_grouping():
            logging.warning(f"Sinks of type {cls._get_sink_type()} do not support notification grouping")
        return values

    @classmethod
    def __parse_dict_matchers(cls, matchers) -> Union[Dict, List[Dict]]:
        if isinstance(matchers, List):
            return [cls.__selectors_dict(matcher) for matcher in matchers]
        else:
            return cls.__selectors_dict(matchers)

    @staticmethod
    def __selectors_dict(selectors: str) -> Dict:
        parts = selectors.split(",")
        result = {}
        for part in parts:
            kv = part.strip().split("=")
            if len(kv) != 2:
                logging.error(f"Illegal labels matchers {selectors}. Matcher is ignored.")
                return {}
            result[kv[0].strip()] = kv[1].strip()
        return result

    @classmethod
    def _supports_grouping(cls):
        return False

    @classmethod
    @abstractmethod
    def _get_sink_type(cls):
        raise NotImplementedError
