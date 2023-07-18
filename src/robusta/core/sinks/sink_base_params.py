import logging
from typing import Dict, List, Union

from pydantic import BaseModel, root_validator

from robusta.core.playbooks.playbook_utils import replace_env_vars_values


class SinkBaseParams(BaseModel):
    name: str
    send_svg: bool = False
    default: bool = True
    match: dict = {}

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
