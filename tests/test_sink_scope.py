import unittest.mock
from typing import Dict, List, Optional
from unittest.mock import Mock

import pytest
import yaml
from pydantic import BaseModel

from robusta.core.reporting import Finding, FindingSeverity, FindingSource, FindingSubject
from robusta.core.reporting.consts import FindingSubjectType, FindingType
from robusta.core.sinks.sink_base import SinkBase
from robusta.core.sinks.sink_base_params import ScopeParams, SinkBaseParams


class CheckFindingSubject(BaseModel):
    name: Optional[str] = "pod-xxx-yyy"
    namespace: Optional[str] = "default"
    kind: Optional[FindingSubjectType] = FindingSubjectType.TYPE_POD
    node: Optional[str] = None


class CheckFinding(BaseModel):
    title: str = "test finding"
    subject: CheckFindingSubject = CheckFindingSubject()
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    aggregation_key: str = "oom_kill"
    severity: FindingSeverity = FindingSeverity.INFO
    source: FindingSource = FindingSource.NONE
    finding_type: FindingType = FindingType.ISSUE

    def create_finding(self) -> Finding:
        subject = FindingSubject(
            name=self.subject.name,
            namespace=self.subject.namespace,
            subject_type=self.subject.kind,
            node=self.subject.node,
            labels=self.labels,
            annotations=self.annotations,
        )
        return Finding(
            title=self.title,
            subject=subject,
            aggregation_key=self.aggregation_key,
            severity=self.severity,
            source=self.source,
            finding_type=self.finding_type,
        )


class ScopeCheck(BaseModel):
    finding: CheckFinding
    expected: bool
    message: str


class ScopeTest(BaseModel):
    scope: ScopeParams
    checks: List[ScopeCheck]


class TestConfig(BaseModel):
    tests: List[ScopeTest]


class TestScopeParams:
    def test_scope_params_inc_and_exc_missing(self):
        with pytest.raises(ValueError):
            ScopeParams(include=None, exclude=None)

    @pytest.mark.parametrize(
        "include,exclude",
        [
            (None, []),
            ([], None),
            ([], []),
        ],
    )
    def test_scope_params_empty_inc_exc(self, include, exclude):
        with pytest.raises(ValueError):
            ScopeParams(include=include, exclude=exclude)

    @pytest.mark.parametrize(
        "include_data,exclude_data,expected_include_data,expected_exclude_data",
        [
            (
                None,
                [{"labels": "xyz", "name": ["1", "2"]}],
                None,
                [{"labels": ["xyz"], "name": ["1", "2"]}],
            ),
            (
                [{"name": ".*", "labels": ["1", "2"]}],
                None,
                [{"name": [".*"], "labels": ["1", "2"]}],
                None,
            ),
        ],
    )
    def test_scope_params_normalization(self, include_data, exclude_data, expected_include_data, expected_exclude_data):
        params = ScopeParams(include=include_data, exclude=exclude_data)
        assert params.include == expected_include_data
        assert params.exclude == expected_exclude_data


class TestSinkBase:
    @pytest.mark.parametrize("matches_result,expected_result", [(True, True), (False, False)])
    def test_accepts(self, matches_result, expected_result):
        sink_base = SinkBase(sink_params=SinkBaseParams(name="x"), registry=Mock())
        finding = Finding(title="y", aggregation_key="aaa")
        finding.matches = Mock(return_value=matches_result)
        # sink_base.time_slices is [TimeSliceAlways()] here, so the result will depend
        # solely on matches_result.
        assert sink_base.accepts(finding) is expected_result


class TestFilterable:
    @pytest.fixture()
    def get_invalid_attributes(self):
        return Mock(return_value=[])

    @pytest.fixture()
    def finding(self, get_invalid_attributes):
        finding = Finding(title="title", aggregation_key="ag_key")
        with unittest.mock.patch.object(finding, "get_invalid_attributes", get_invalid_attributes):
            yield finding

    @pytest.fixture()
    def finding_with_data(self, finding):
        finding.subject.labels = {"a": "x", "b": "fffy"}
        finding.subject.namespace = "ns12"
        finding.title = "c1"
        return finding

    def test_matches_no_scope_req(self, finding):
        with unittest.mock.patch.object(finding, "scope_inc_exc_matches", Mock()) as mock_scope_inc_exc_matches:
            finding.matches({}, None)
            mock_scope_inc_exc_matches.assert_not_called()
            finding.get_invalid_attributes.assert_called_once()

    @pytest.mark.parametrize(
        "include,exclude,expected_output,match_req_evaluated",
        [
            ([{"labels": "a=x,b=.*y"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}], None, True, True),
            ([{"labels": "a=q,b=.*y"}, {"namespace": "ns12"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}, {"title": "c1"}], None, True, False),
            ([{"labels": "a=q,b=.*y"}, {"title": "d[1-9]*"}], None, True, True),
            (None, [{"labels": "a=x,b=.*y"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"namespace": "ns12"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"title": "c[1-9]"}], False, False),
            (None, [{"labels": "a=q,b=.*y"}, {"title": "d[1-9]*"}], True, True),
            ([{"namespace": "ns"}], None, True, False),
            (None, [{"namespace": "ns"}], True, False),
        ],
    )
    def test_matches_inc_match(
        self,
        finding_with_data,
        get_invalid_attributes,
        include,
        exclude,
        expected_output,
        match_req_evaluated,
    ):
        assert finding_with_data.matches({}, ScopeParams(include=include, exclude=exclude)) is expected_output
        # The asserts below check that the result has/has not been computed using scope params only and
        # that match_requirements were not evaluated. It's not the cleanest, but to make it so would
        # require major refactorings in Finding/Filterable.
        if match_req_evaluated:
            get_invalid_attributes.assert_called_once()
        else:
            get_invalid_attributes.assert_not_called()

    def test_matches_unknown_attr(self, finding_with_data):
        with pytest.raises(ValueError):
            finding_with_data.matches({}, ScopeParams(include=[{"xyzzfoo": "123"}], exclude=None))

    def test_sink_scopes(self, finding):
        with open("./scope_test_config.yaml") as test_config_file:
            test_config = TestConfig(**yaml.safe_load(test_config_file))

        for scope_test in test_config.tests:
            sink_base = SinkBase(sink_params=SinkBaseParams(name="x", scope=scope_test.scope), registry=Mock())

            for check in scope_test.checks:
                finding = check.finding.create_finding()
                assert sink_base.accepts(finding) is check.expected, check.message
