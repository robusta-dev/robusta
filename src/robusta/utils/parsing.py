import datetime
import json
import logging
from typing import Any, Union


def load_json(s: Union[str, bytes]) -> Any:
    """
    Like json.loads() but prints the input if parsing fails
    """
    try:
        return json.loads(s)
    except json.decoder.JSONDecodeError:
        sep = "----------------"
        logging.error(f"could not parse json:\n{sep}\n{s}\n{sep}\n")
        raise


def datetime_to_db_str(datetime_obj: datetime.datetime) -> str:
    """
    Return datetime string (DB parsable)
    """
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:%S.%f%z")

def normalize_datetime(date_string: str) -> str:
    splitted = date_string.split(".")
    if "Z" in splitted[1].upper() and len(splitted[1]) > 6:
        splitted_seconds = splitted[1].split("z")
        truncated_seconds = f"{splitted_seconds[0][:6]}Z"
        date_string = f"{splitted[0]}.{truncated_seconds}"

    return date_string
