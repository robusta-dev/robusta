import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, root_validator

ScopeIncludeExcludeParamsT = Dict[str, Optional[Union[str, List[str]]]]


class ScopeParams(BaseModel):
    include: Optional[List[ScopeIncludeExcludeParamsT]]
    exclude: Optional[List[ScopeIncludeExcludeParamsT]]

    @root_validator
    def check_non_empty(cls, data: Dict) -> Dict:
        if not (data.get("include") is not None or data.get("exclude") is not None):
            raise ValueError("scope requires include and/or exclude subfield")
        return data

    @root_validator
    def check_and_normalize(cls, data: Dict) -> Dict:
        """Check and normalize entries inside include/exclude"""
        for key in ["include", "exclude"]:
            entry = data.get(key)
            if entry is None:
                continue
            if entry == []:
                raise ValueError("scope include/exclude specification requires at least one matcher")
            for inc_exc_params in entry:
                for attr_name, regex_or_regexes in inc_exc_params.items():
                    if isinstance(regex_or_regexes, str):
                        regex_or_regexes = [regex_or_regexes]
                    inc_exc_params[attr_name] = regex_or_regexes
        return data


class BaseScopeMatcher(ABC):
    @abstractmethod
    def get_data(self) -> Dict:
        raise NotImplementedError

    def scope_inc_exc_matches(self, scope_inc_exc: List[ScopeIncludeExcludeParamsT]) -> bool:
        return any(self.scope_matches(scope) for scope in scope_inc_exc)

    def scope_matches(self, scope: ScopeIncludeExcludeParamsT) -> bool:
        # scope is e.g. {'labels': ['app=oomki.*,app!=X.*Y']}
        # or {'name': ['pod-xyz.*'], 'title': ['fdc.*a', 'fdd.*b'], 'type': ['ISSUE']}
        for attr_name, attr_matchers in scope.items():
            if not self.scope_attribute_matches(attr_name, attr_matchers):
                return False
        return True

    def match_attribute(self, attr_name: str, attr_value, attr_matcher: str) -> bool:
        if attr_name == "attributes":
            return self.scope_match_attributes(attr_matcher, attr_value)
        elif attr_name == "namespace_labels":
            return self.scope_match_namespace_labels(attr_matcher, attr_value)
        elif attr_name in ["labels", "annotations"]:
            return self.match_labels_annotations(attr_matcher, attr_value)
        elif re.fullmatch(attr_matcher, attr_value):
            return True
        return False

    def scope_attribute_matches(self, attr_name: str, attr_matchers: List[str]) -> bool:
        data = self.get_data()
        if attr_name not in data:
            logging.warning(f'Scope match on non-existent attribute "{attr_name}" ({data=})')
            return False
        attr_value = data[attr_name]
        return any([self.match_attribute(attr_name, attr_value, matcher) for matcher in attr_matchers])

    def scope_match_attributes(self, attr_matcher: str, attr_value: Dict[str, Union[List, Dict]]) -> bool:
        raise NotImplementedError

    def scope_match_namespace_labels(self, attr_matcher: str, attr_value: Dict[str, Union[List, Dict]]) -> bool:
        raise NotImplementedError

    def match_labels_annotations(self, labels_match_expr: str, labels: Dict[str, str]) -> bool:
        for label_match in labels_match_expr.split(","):
            if not self.label_matches(label_match, labels):
                return False
        return True

    def label_matches(self, label_match: str, labels: Dict[str, str]) -> bool:
        label_name, label_regex = label_match.split("=", 1)
        label_name = label_name.strip()
        label_regex = label_regex.strip()
        if label_name.endswith("!"):  # label_name!=match_expr
            label_name = label_name[:-1].rstrip()
            expect_match = False
        else:
            expect_match = True
        label_value = labels.get(label_name)
        if label_value is None:  # no label with that name
            return False
        return bool(re.fullmatch(label_regex, label_value.strip())) == expect_match
