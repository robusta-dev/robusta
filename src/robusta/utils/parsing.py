import datetime
import json
import logging
from collections import defaultdict
from string import Template
from typing import Any, Dict, Union

from hikaru.model.rel_1_26 import ObjectReference

from robusta.core.reporting import FindingSubject


def format_event_templated_string(subject: Union[FindingSubject, ObjectReference], string_to_substitute) -> str:
    """
        For templating strings based on event subjects
    """
    labels: Dict[str, str] = defaultdict(lambda: "<missing>")
    kind = subject.kind if isinstance(subject, ObjectReference) else subject.subject_type.value
    labels.update(
        {
            "name": subject.name,
            "kind": kind,
            "namespace": subject.namespace if subject.namespace else "<missing>",
            "node": subject.node if isinstance(subject, FindingSubject) and subject.node else "<missing>",
        }
    )
    return Template(string_to_substitute).safe_substitute(labels)

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
