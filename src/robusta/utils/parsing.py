import json
import logging
from typing import Union, Any


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
