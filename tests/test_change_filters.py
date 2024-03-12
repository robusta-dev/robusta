import json
from typing import Optional

import hikaru
import pytest
from hikaru import DiffDetail

from robusta.core.model.k8s_operation_type import K8sOperationType
from robusta.core.playbooks.base_trigger import BaseTrigger, DEFAULT_CHANGE_IGNORE, DEFAULT_CHANGE_INCLUDE
from robusta.integrations.kubernetes.base_event import K8sBaseChangeEvent


class TestBaseTrigger:
    @pytest.mark.parametrize(
        "input_change_filters,expected_change_filters",
        [
            (None, {"include": DEFAULT_CHANGE_INCLUDE, "ignore": DEFAULT_CHANGE_IGNORE}),
            ({"include": ["a", "b"]}, {"include": ["a", "b"], "ignore": DEFAULT_CHANGE_IGNORE}),
            ({"ignore": ["c", "d"]}, {"include": DEFAULT_CHANGE_INCLUDE, "ignore": ["c", "d"]}),
            ({"include": ["x", "y"], "ignore": ["p", "q"]}, {"include": ["x", "y"], "ignore": ["p", "q"]}),
        ],
    )
    def test_init(self, input_change_filters, expected_change_filters):
        trigger = BaseTrigger(change_filters=input_change_filters)
        assert trigger.change_filters == expected_change_filters

    @pytest.fixture()
    def event(self):
        with open("tests/k8s_change_obj.json") as f:
            data = json.loads(f.read())
        return K8sBaseChangeEvent(
            operation=K8sOperationType.UPDATE,
            old_obj=hikaru.from_dict(data),
            obj=hikaru.from_dict(data),
        )

    @pytest.fixture()
    def trigger(self):
        return BaseTrigger()  # change_filters initialized to defaults

    def _set_attr_by_path(self, obj, field_path: str, new_val):
        attr_path = field_path.split(".")
        for attr_name in attr_path[:-1]:
            obj = getattr(obj, attr_name)
        setattr(obj, attr_path[-1], new_val)

    @pytest.mark.parametrize("change_field", [None] + DEFAULT_CHANGE_IGNORE)
    def test_check_change_filters_no_change(self, change_field: Optional[str], event, trigger):
        if change_field:
            self._set_attr_by_path(event.obj, change_field, 987654321)
        assert trigger.check_change_filters(event) is False
        assert not hasattr(event, "obj_filtered")
        assert not hasattr(event, "old_obj_filtered")
        assert not hasattr(event, "filtered_diffs")

    @pytest.mark.parametrize(
        "change_field,new_value,old_value,expected_change_path,expected_diff_new_value",
        [
            ("spec.selector.matchLabels", {"app": "X"}, "xxx", "Deployment.spec.selector.matchLabels['app']", "X"),
            ("spec.progressDeadlineSeconds", 300, 600, "Deployment.spec.progressDeadlineSeconds", 300),
            ("spec.revisionHistoryLimit", 15, 10, "Deployment.spec.revisionHistoryLimit", 15),
        ],
    )
    def test_check_change_filters_changes(
        self, change_field: str, new_value, old_value, expected_change_path, expected_diff_new_value, event, trigger
    ):
        self._set_attr_by_path(event.obj, change_field, new_value)
        assert trigger.check_change_filters(event) is True
        assert hasattr(event, "obj_filtered")
        assert hasattr(event, "old_obj_filtered")
        assert all(isinstance(diff, DiffDetail) for diff in event.filtered_diffs)
        diff = event.filtered_diffs[0]
        assert diff.formatted_path == expected_change_path
        assert diff.other_value == old_value
        assert diff.value == expected_diff_new_value
